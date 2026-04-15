import math
from datetime import datetime, timedelta

class AntigravityEngine:
    def __init__(self, db_connection):
        self.db = db_connection

    def fetch_devaluation_trend(self):
        cursor = self.db.cursor()
        # Fetch last 30 valid days of DolarBCV
        query = """
            SELECT TOP 30 dolarbcv 
            FROM EnterpriseAdmin_AMC.dbo.dolartoday WITH (NOLOCK)
            WHERE dolarbcv IS NOT NULL AND dolarbcv > 0
            ORDER BY fecha DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if len(rows) < 2:
            return 0.001, 0.0001, 40.0 # safety fallback
            
        historic = [float(r[0]) for r in reversed(rows)]
        current_tc = historic[-1]
        
        returns = [(historic[i] - historic[i-1]) / historic[i-1] for i in range(1, len(historic))]
        avg_devaluation = sum(returns) / len(returns)
        if avg_devaluation < 0:
             avg_devaluation = 0.0005 # Force small positive to assume slight inflation if negative noise
             
        volatility = math.sqrt(sum((r - avg_devaluation)**2 for r in returns) / len(returns))
        
        return avg_devaluation, volatility, current_tc

    def project_tc(self, t_days, r_dev, current_tc):
        # We assume exponential devaluation
        return current_tc * ((1 + r_dev) ** t_days)

    def calculate_opportunity_cost(self, invoice, t_pay, r_dev, current_tc):
        """
        Calculates the real cost in USD equivalent if paying on 't_pay' days from now.
        Evaluates discount tiers and indexation tolerance.
        """
        P = invoice["nominal_bs"]
        discount = 0.0
        
        # Determine discount based on payment day vs emission day difference
        # t_pay is from TODAY. We need days from EMISSION.
        days_from_emission = invoice["days_elapsed_since_emission"] + t_pay
        
        for d in invoice.get("descuentos", []):
            if d["DiasDesde"] <= days_from_emission <= d["DiasHasta"]:
                discount = d["Porcentaje"]
                break
                
        # Base Commercial Discount
        desc_base = 0.0
        if invoice.get("desc_base_cond") == "VENCIMIENTO":
            if days_from_emission <= invoice["t_due"]:
                desc_base = invoice.get("desc_base_pct", 0.0)
        else:
            # Independent
            desc_base = invoice.get("desc_base_pct", 0.0)
            
        amount_bs = P * (1.0 - desc_base) * (1.0 - discount)
        tc_pay_future = self.project_tc(t_pay, r_dev, current_tc)
        
        # Check indexation tolerance
        if days_from_emission > invoice["t_tolerance"]:
            # Indexed. It means original nominal debt stays anchored in USD from emission or specific date
            # Assuming anchored to emission date
            tc_emision = invoice["tc_emision"]
            if tc_emision and tc_emision > 0:
                amount_bs = amount_bs * (tc_pay_future / tc_emision)
                
        usd_cost = amount_bs / tc_pay_future
        return amount_bs, usd_cost

    def optimize_payable_schedule(self, cashflow_timeline, invoices, percentage_flow_margin):
        """
        - cashflow_timeline: list of dicts with 'Periodo', 'SaldoRealCajaUSD'
        - invoices: list of open invoices and their constraints
        - percentage_flow_margin: float 0 to 1 (e.g. 0.90 for 90% usage)
        """
        r_dev, vol, current_tc = self.fetch_devaluation_trend()
        
        options = []
        for inv in invoices:
            costs = []
            
            # Days remaining until due date from today
            days_to_due = max(0, inv["t_due"] - inv["days_elapsed_since_emission"])
            if days_to_due > 120:
                days_to_due = 120 # Cap search space safety
                
            for t in range(0, days_to_due + 1):
                amt_bs, usd_cost = self.calculate_opportunity_cost(inv, t, r_dev, current_tc)
                costs.append((t, amt_bs, usd_cost))
            
            if not costs:
                continue
                
            # Sort by lowest USD cost. 
            # IMPORTANT: If costs are equal, we pick the LATEST date (preserve liquidity)
            costs.sort(key=lambda x: (round(x[2], 4), -x[0])) 
            
            # Baseline: cost at the final due date (the item with the highest t in the original unsorted list)
            # Since the search loop was for t in range(0, days_to_due + 1), the due date is the highest t.
            # We re-extract it for baseline comparison.
            t_due_limit = max(c[0] for c in costs)
            baseline_cost = next(c[2] for c in costs if c[0] == t_due_limit)
            
            best_t, best_amt_bs, best_usd = costs[0]
            
            # Real USD savings: how much we save by paying now/best_t vs waiting until the forced due date.
            # Only positive if there's a real financial benefit (e.g. Discount > Devaluation).
            real_savings_usd = max(0, baseline_cost - best_usd)
            
            options.append({
                "invoice": inv,
                "costs": costs,
                "max_savings_usd": real_savings_usd
            })
            
        # Priority mapping
        priority_weight = {"Alta": 3, "Media": 2, "Baja": 1}
        # In this project, if priority doesn't exist, default to Media (2)
        options.sort(key=lambda x: (priority_weight.get(x["invoice"].get("priority", "Media"), 2), x["max_savings_usd"]), reverse=True)
        
        # Liquidity map from CTE projection
        # The CTE provides cumulative SaldoRealCajaUSD by date.
        # We can map 't' (days from today) to a maximum allowed spend.
        from datetime import date
        today = date.today()
        
        liquidity_map = {} # T -> allowed capacity in USD
        for c in cashflow_timeline:
            try:
                date_obj = datetime.strptime(c["Periodo"], "%Y-%M-%d").date() if "-" in c["Periodo"] else None
            except:
                pass
            
            if "-" in c["Periodo"]:
                try:
                    c_year, c_month, c_day = map(int, c["Periodo"].split('-'))
                    date_obj = date(c_year, c_month, c_day)
                    t_diff = (date_obj - today).days
                    if t_diff >= 0:
                        raw_usd = float(c["SaldoRealCajaUSD"] or 0)
                        # Apply Percentage constraint logic! Note: 90% means we can ONLY use 90% of the projected cash
                        liquidity_map[t_diff] = max(0, raw_usd * percentage_flow_margin)
                except Exception as e:
                    pass

        # If cache is missing days, fallback
        max_t = max([c[0] for opt in options for c in opt["costs"]]) if options else 0
        for t in range(max_t + 1):
            if t not in liquidity_map:
                # fill forward
                prev_t = t - 1
                while prev_t >= 0 and prev_t not in liquidity_map:
                    prev_t -= 1
                liquidity_map[t] = liquidity_map.get(prev_t, 0)
        
        schedule = []
        daily_spent_usd = {t: 0.0 for t in range(max_t + 5)}
        
        total_savings_usd = 0
        total_cost_usd = 0
        
        for opt in options:
            inv = opt["invoice"]
            assigned = False
            
            for cost_item in opt["costs"]:
                t, amt_bs, usd_cost = cost_item
                
                # Check liquidity
                available = liquidity_map.get(t, 0.0) - daily_spent_usd[t]
                
                if usd_cost <= available:
                    # Assign!
                    daily_spent_usd[t] += usd_cost
                    t_due_actual = max(0, inv["t_due"] - inv["days_elapsed_since_emission"])
                    schedule.append({
                        "id": inv["id"],
                        "supplier": inv["supplier"],
                        "date_t": t,
                        "date_str": (today + timedelta(days=t)).isoformat(),
                        "due_date_str": (today + timedelta(days=t_due_actual)).isoformat(),
                        "orig_bs": inv["nominal_bs"],
                        "final_bs": amt_bs,
                        "usd_cost": usd_cost,
                        "savings": opt["max_savings_usd"],
                        "priority": inv.get("priority", "Media")
                    })
                    total_savings_usd += opt["max_savings_usd"]
                    total_cost_usd += usd_cost
                    assigned = True
                    break
                    
            if not assigned:
                # Force to due date, regardless of liquidity (since it must be paid, but we assume loss of savings)
                t_due = max(0, inv["t_due"] - inv["days_elapsed_since_emission"])
                amt_bs, usd_cost = self.calculate_opportunity_cost(inv, t_due, r_dev, current_tc)
                schedule.append({
                    "id": inv["id"],
                    "supplier": inv["supplier"],
                    "date_t": t_due,
                    "date_str": (today + timedelta(days=t_due)).isoformat(),
                    "due_date_str": (today + timedelta(days=t_due)).isoformat(),
                    "orig_bs": inv["nominal_bs"],
                    "final_bs": amt_bs,
                    "usd_cost": usd_cost,
                    "savings": 0.0,
                    "priority": inv.get("priority", "Media"),
                    "note": "Altered due to flow constraint"
                })
                total_cost_usd += usd_cost
                
        return {
            "schedule": schedule,
            "metrics": {
                "r_dev_daily": r_dev,
                "volatility": vol,
                "total_savings_usd": total_savings_usd,
                "total_cost_usd": total_cost_usd
            }
        }
