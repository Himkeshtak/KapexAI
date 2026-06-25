"""Deterministic mortgage and real-estate calculator tools."""

import math

from langchain.tools import tool


def _nonnegative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be zero or greater")


def _positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")


def _payment(
    principal: float,
    annual_rate: float,
    periods: int,
    payments_per_year: int = 12,
) -> float:
    _nonnegative(principal, "principal")
    if periods < 1:
        raise ValueError("periods must be at least 1")
    periodic_rate = annual_rate / payments_per_year
    if periodic_rate <= -1:
        raise ValueError("periodic rate must exceed -100%")
    if periodic_rate == 0:
        return principal / periods
    return (
        principal
        * periodic_rate
        * (1 + periodic_rate) ** periods
        / ((1 + periodic_rate) ** periods - 1)
    )


def _balance_after_payments(
    principal: float,
    annual_rate: float,
    payment: float,
    payments_made: int,
    payments_per_year: int = 12,
) -> float:
    periodic_rate = annual_rate / payments_per_year
    if periodic_rate == 0:
        return max(0.0, principal - payment * payments_made)
    growth = (1 + periodic_rate) ** payments_made
    return max(
        0.0,
        principal * growth - payment * (growth - 1) / periodic_rate,
    )


def _simulate_payoff(
    principal: float,
    annual_rate: float,
    regular_payment: float,
    extra_payment: float = 0.0,
    payments_per_year: int = 12,
    maximum_periods: int = 1200,
) -> dict:
    _positive(regular_payment + extra_payment, "total periodic payment")
    periodic_rate = annual_rate / payments_per_year
    balance = principal
    total_interest = 0.0
    periods = 0
    while balance > 1e-8 and periods < maximum_periods:
        interest = balance * periodic_rate
        payment = min(balance + interest, regular_payment + extra_payment)
        principal_paid = payment - interest
        if principal_paid <= 0:
            raise ValueError("payment is not sufficient to amortize the loan")
        balance -= principal_paid
        total_interest += interest
        periods += 1
    if balance > 1e-8:
        raise ValueError("loan did not amortize within the maximum period")
    return {
        "periods_to_payoff": periods,
        "years_to_payoff": periods / payments_per_year,
        "total_interest": total_interest,
        "total_paid": principal + total_interest,
    }


def _mortgage_summary(
    loan_amount: float,
    annual_rate: float,
    term_years: float,
    payments_per_year: int = 12,
) -> dict:
    periods_float = term_years * payments_per_year
    periods = round(periods_float)
    if not math.isclose(periods_float, periods, abs_tol=1e-9):
        raise ValueError("term_years must produce a whole payment period")
    payment = _payment(
        loan_amount, annual_rate, periods, payments_per_year
    )
    total_paid = payment * periods
    return {
        "periodic_payment": payment,
        "number_of_payments": periods,
        "total_paid": total_paid,
        "total_interest": total_paid - loan_amount,
    }


@tool
def three_x_rent_calculator(
    monthly_rent: float, gross_monthly_income: float
) -> dict:
    """Evaluate a common rental screening rule requiring income of three times rent."""
    required_income = monthly_rent * 3
    return {
        "required_monthly_income": required_income,
        "actual_monthly_income": gross_monthly_income,
        "qualifies": gross_monthly_income >= required_income,
        "income_to_rent_multiple": (
            gross_monthly_income / monthly_rent if monthly_rent else None
        ),
    }


@tool
def affo_calculator(
    net_income: float,
    depreciation_and_amortization: float,
    gains_on_property_sales: float,
    recurring_capital_expenditures: float,
    straight_line_rent_adjustment: float = 0.0,
    other_adjustments: float = 0.0,
) -> dict:
    """Calculate REIT adjusted funds from operations."""
    ffo = net_income + depreciation_and_amortization - gains_on_property_sales
    affo = (
        ffo
        - recurring_capital_expenditures
        - straight_line_rent_adjustment
        + other_adjustments
    )
    return {"funds_from_operations": ffo, "adjusted_funds_from_operations": affo}


@tool
def arm_mortgage_calculator(
    loan_amount: float,
    initial_annual_rate: float,
    initial_fixed_years: float,
    total_term_years: float,
    adjusted_annual_rate: float,
) -> dict:
    """Calculate initial and first adjusted payments for an adjustable-rate mortgage."""
    total_periods = round(total_term_years * 12)
    fixed_periods = round(initial_fixed_years * 12)
    initial_payment = _payment(
        loan_amount, initial_annual_rate, total_periods
    )
    balance = _balance_after_payments(
        loan_amount,
        initial_annual_rate,
        initial_payment,
        fixed_periods,
    )
    remaining_periods = total_periods - fixed_periods
    if remaining_periods < 1:
        raise ValueError("initial_fixed_years must be less than total_term_years")
    adjusted_payment = _payment(
        balance, adjusted_annual_rate, remaining_periods
    )
    return {
        "initial_monthly_payment": initial_payment,
        "balance_at_first_adjustment": balance,
        "adjusted_monthly_payment": adjusted_payment,
        "payment_change": adjusted_payment - initial_payment,
    }


@tool
def arv_calculator(
    comparable_after_repair_values: list[float],
    total_comparable_adjustments: float = 0.0,
    repair_cost: float | None = None,
) -> dict:
    """Estimate after-repair value from comparable values and adjustments."""
    if not comparable_after_repair_values:
        raise ValueError("At least one comparable value is required")
    arv = (
        sum(comparable_after_repair_values)
        / len(comparable_after_repair_values)
        + total_comparable_adjustments
    )
    return {
        "after_repair_value": arv,
        "repair_cost": repair_cost,
        "arv_less_repairs": arv - repair_cost if repair_cost is not None else None,
    }


@tool
def adr_calculator(
    room_revenue: float, rooms_sold: float
) -> dict:
    """Calculate hospitality average daily room rate."""
    _positive(rooms_sold, "rooms_sold")
    return {"average_daily_rate": room_revenue / rooms_sold}


@tool
def biweekly_mortgage_calculator(
    loan_amount: float,
    annual_rate: float,
    term_years: float,
) -> dict:
    """Compare standard monthly mortgage payments with accelerated biweekly payments."""
    monthly = _mortgage_summary(
        loan_amount, annual_rate, term_years, 12
    )
    biweekly_payment = monthly["periodic_payment"] / 2
    accelerated = _simulate_payoff(
        loan_amount,
        annual_rate,
        biweekly_payment,
        payments_per_year=26,
    )
    return {
        "standard_monthly_payment": monthly["periodic_payment"],
        "biweekly_payment": biweekly_payment,
        "biweekly_payoff_years": accelerated["years_to_payoff"],
        "biweekly_total_interest": accelerated["total_interest"],
        "interest_saved": monthly["total_interest"] - accelerated["total_interest"],
    }


@tool
def biweekly_mortgage_payment_calculator(
    monthly_mortgage_payment: float
) -> dict:
    """Convert a monthly mortgage payment into an accelerated biweekly payment."""
    return {
        "biweekly_payment": monthly_mortgage_payment / 2,
        "annual_amount_paid": monthly_mortgage_payment / 2 * 26,
        "equivalent_monthly_payments_per_year": 13,
    }


@tool
def cap_rate_calculator(
    annual_net_operating_income: float, property_value: float
) -> dict:
    """Calculate real-estate capitalization rate."""
    _positive(property_value, "property_value")
    rate = annual_net_operating_income / property_value
    return {"capitalization_rate": rate, "cap_rate_percent": rate * 100}


@tool
def commercial_lease_calculator(
    rentable_square_feet: float,
    annual_base_rent_per_square_foot: float,
    annual_cam_per_square_foot: float = 0.0,
    annual_tax_per_square_foot: float = 0.0,
    annual_insurance_per_square_foot: float = 0.0,
) -> dict:
    """Calculate annual and monthly commercial occupancy cost."""
    annual_base = rentable_square_feet * annual_base_rent_per_square_foot
    pass_throughs = rentable_square_feet * (
        annual_cam_per_square_foot
        + annual_tax_per_square_foot
        + annual_insurance_per_square_foot
    )
    annual_total = annual_base + pass_throughs
    return {
        "annual_base_rent": annual_base,
        "annual_pass_throughs": pass_throughs,
        "annual_occupancy_cost": annual_total,
        "monthly_occupancy_cost": annual_total / 12,
    }


@tool
def down_payment_calculator(
    purchase_price: float, down_payment_rate: float
) -> dict:
    """Calculate down payment and resulting base loan amount."""
    if not 0 <= down_payment_rate <= 1:
        raise ValueError("down_payment_rate must be between 0 and 1")
    down_payment = purchase_price * down_payment_rate
    return {
        "down_payment": down_payment,
        "loan_amount": purchase_price - down_payment,
        "loan_to_value_ratio": 1 - down_payment_rate,
    }


@tool
def earnest_money_calculator(
    purchase_price: float, earnest_money_rate: float
) -> dict:
    """Calculate earnest-money deposit from purchase price."""
    return {
        "earnest_money": purchase_price * earnest_money_rate,
        "remaining_price_before_other_credits": purchase_price
        * (1 - earnest_money_rate),
    }


@tool
def fha_loan_calculator(
    home_price: float,
    down_payment_rate: float,
    annual_interest_rate: float,
    term_years: float,
    upfront_mip_rate: float = 0.0175,
    annual_mip_rate: float = 0.0055,
    finance_upfront_mip: bool = True,
) -> dict:
    """Estimate FHA loan amount, mortgage payment, and mortgage insurance."""
    base_loan = home_price * (1 - down_payment_rate)
    upfront_mip = base_loan * upfront_mip_rate
    financed_loan = base_loan + upfront_mip if finance_upfront_mip else base_loan
    mortgage = _mortgage_summary(
        financed_loan, annual_interest_rate, term_years
    )
    monthly_mip = base_loan * annual_mip_rate / 12
    return {
        "down_payment": home_price * down_payment_rate,
        "base_loan_amount": base_loan,
        "upfront_mip": upfront_mip,
        "financed_loan_amount": financed_loan,
        "monthly_principal_and_interest": mortgage["periodic_payment"],
        "estimated_monthly_mip": monthly_mip,
        "estimated_monthly_payment_before_taxes_and_insurance": (
            mortgage["periodic_payment"] + monthly_mip
        ),
        "caution": "FHA limits and MIP duration depend on current HUD rules and loan terms.",
    }


@tool
def gift_of_equity_calculator(
    appraised_value: float,
    sale_price: float,
    cash_down_payment: float = 0.0,
) -> dict:
    """Calculate gift of equity and effective equity contribution."""
    gift = max(0.0, appraised_value - sale_price)
    return {
        "gift_of_equity": gift,
        "total_equity_contribution": gift + cash_down_payment,
        "effective_loan_to_value_before_closing_costs": (
            (sale_price - cash_down_payment) / appraised_value
            if appraised_value
            else None
        ),
    }


@tool
def gross_rent_multiplier_calculator(
    property_price: float, gross_annual_rent: float
) -> dict:
    """Calculate gross rent multiplier."""
    _positive(gross_annual_rent, "gross_annual_rent")
    return {"gross_rent_multiplier": property_price / gross_annual_rent}


@tool
def mortgage_payoff_calculator(
    current_balance: float,
    annual_interest_rate: float,
    monthly_payment: float,
    additional_monthly_payment: float = 0.0,
) -> dict:
    """Calculate mortgage payoff time and total remaining interest."""
    return _simulate_payoff(
        current_balance,
        annual_interest_rate,
        monthly_payment,
        additional_monthly_payment,
    )


@tool
def mortgage_penalty_calculator(
    outstanding_balance: float,
    contract_annual_rate: float,
    comparison_annual_rate: float,
    remaining_term_months: int,
    months_interest_penalty: int = 3,
    penalty_method: str = "greater",
) -> dict:
    """Estimate a mortgage break penalty from three-month interest and IRD."""
    three_month_interest = (
        outstanding_balance
        * contract_annual_rate
        * months_interest_penalty
        / 12
    )
    interest_rate_differential = max(
        0.0,
        outstanding_balance
        * (contract_annual_rate - comparison_annual_rate)
        * remaining_term_months
        / 12,
    )
    if penalty_method == "lesser":
        penalty = min(three_month_interest, interest_rate_differential)
    else:
        penalty = max(three_month_interest, interest_rate_differential)
    return {
        "three_month_interest": three_month_interest,
        "interest_rate_differential": interest_rate_differential,
        "estimated_penalty": penalty,
        "caution": "Actual lender penalty formulas and discounts vary by contract.",
    }


@tool
def mortgage_points_calculator(
    loan_amount: float,
    points: float,
    monthly_payment_savings: float = 0.0,
) -> dict:
    """Calculate upfront mortgage point cost and optional break-even period."""
    cost = loan_amount * points / 100
    return {
        "points_cost": cost,
        "break_even_months": (
            cost / monthly_payment_savings
            if monthly_payment_savings > 0
            else None
        ),
    }


@tool
def mortgage_prepayment_calculator(
    current_balance: float,
    annual_interest_rate: float,
    regular_monthly_payment: float,
    extra_monthly_payment: float,
) -> dict:
    """Compare mortgage payoff with and without recurring prepayments."""
    baseline = _simulate_payoff(
        current_balance, annual_interest_rate, regular_monthly_payment
    )
    accelerated = _simulate_payoff(
        current_balance,
        annual_interest_rate,
        regular_monthly_payment,
        extra_monthly_payment,
    )
    return {
        "baseline": baseline,
        "with_prepayment": accelerated,
        "months_saved": baseline["periods_to_payoff"]
        - accelerated["periods_to_payoff"],
        "interest_saved": baseline["total_interest"]
        - accelerated["total_interest"],
    }


@tool
def mortgage_rate_calculator(
    loan_amount: float,
    monthly_payment: float,
    term_years: float,
) -> dict:
    """Solve nominal annual mortgage rate from loan, payment, and term."""
    periods = round(term_years * 12)
    _positive(loan_amount, "loan_amount")
    if monthly_payment * periods < loan_amount:
        raise ValueError("payment is too low even for a zero-interest loan")
    lower = 0.0
    upper = 1.0
    for _ in range(200):
        midpoint = (lower + upper) / 2
        calculated = _payment(loan_amount, midpoint, periods)
        if abs(calculated - monthly_payment) < 1e-10:
            break
        if calculated < monthly_payment:
            lower = midpoint
        else:
            upper = midpoint
    annual_rate = (lower + upper) / 2
    return {
        "nominal_annual_rate": annual_rate,
        "annual_rate_percent": annual_rate * 100,
    }


@tool
def mortgage_refinance_calculator(
    current_balance: float,
    current_annual_rate: float,
    current_remaining_years: float,
    new_annual_rate: float,
    new_term_years: float,
    closing_costs: float,
) -> dict:
    """Compare current mortgage payments with a proposed refinance."""
    current = _mortgage_summary(
        current_balance, current_annual_rate, current_remaining_years
    )
    new = _mortgage_summary(
        current_balance, new_annual_rate, new_term_years
    )
    monthly_savings = current["periodic_payment"] - new["periodic_payment"]
    return {
        "current_monthly_payment": current["periodic_payment"],
        "new_monthly_payment": new["periodic_payment"],
        "monthly_savings": monthly_savings,
        "break_even_months": (
            closing_costs / monthly_savings if monthly_savings > 0 else None
        ),
        "current_remaining_interest": current["total_interest"],
        "new_interest_plus_costs": new["total_interest"] + closing_costs,
    }


@tool
def net_effective_rent_calculator(
    monthly_face_rent: float,
    lease_months: int,
    free_rent_months: float = 0.0,
    tenant_improvement_credit: float = 0.0,
    other_concessions: float = 0.0,
) -> dict:
    """Calculate net effective monthly rent after concessions."""
    if lease_months < 1:
        raise ValueError("lease_months must be at least 1")
    gross_contract_rent = monthly_face_rent * lease_months
    concessions = (
        monthly_face_rent * free_rent_months
        + tenant_improvement_credit
        + other_concessions
    )
    net_contract_rent = gross_contract_rent - concessions
    return {
        "gross_contract_rent": gross_contract_rent,
        "total_concessions": concessions,
        "net_contract_rent": net_contract_rent,
        "net_effective_monthly_rent": net_contract_rent / lease_months,
    }


@tool
def net_operating_income_calculator(
    gross_operating_income: float,
    vacancy_and_credit_loss: float,
    operating_expenses: float,
    other_operating_income: float = 0.0,
) -> dict:
    """Calculate property net operating income before financing and income tax."""
    effective_gross_income = (
        gross_operating_income
        - vacancy_and_credit_loss
        + other_operating_income
    )
    return {
        "effective_gross_income": effective_gross_income,
        "net_operating_income": effective_gross_income - operating_expenses,
    }


@tool
def occupancy_rate_calculator(
    occupied_units_or_rooms: float, available_units_or_rooms: float
) -> dict:
    """Calculate occupancy and vacancy rates."""
    _positive(available_units_or_rooms, "available_units_or_rooms")
    rate = occupied_units_or_rooms / available_units_or_rooms
    return {"occupancy_rate": rate, "vacancy_rate": 1 - rate}


@tool
def pag_ibig_housing_loan_calculator(
    loan_amount_php: float,
    annual_interest_rate: float,
    term_years: float,
) -> dict:
    """Estimate Pag-IBIG-style housing loan payment using supplied current rate."""
    result = _mortgage_summary(
        loan_amount_php, annual_interest_rate, term_years
    )
    result["currency"] = "PHP"
    result["caution"] = "Use the borrower's actual Pag-IBIG repricing period and approved rate."
    return result


@tool
def pmi_calculator(
    home_value: float,
    loan_amount: float,
    annual_pmi_rate: float,
) -> dict:
    """Estimate private mortgage insurance from loan-to-value and PMI rate."""
    _positive(home_value, "home_value")
    annual_pmi = loan_amount * annual_pmi_rate
    return {
        "loan_to_value_ratio": loan_amount / home_value,
        "annual_pmi": annual_pmi,
        "monthly_pmi": annual_pmi / 12,
    }


@tool
def price_per_square_foot_calculator(
    property_price: float, square_feet: float
) -> dict:
    """Calculate property price per square foot."""
    _positive(square_feet, "square_feet")
    return {"price_per_square_foot": property_price / square_feet}


@tool
def price_per_square_meter_calculator(
    property_price: float, square_meters: float
) -> dict:
    """Calculate property price per square meter."""
    _positive(square_meters, "square_meters")
    return {"price_per_square_meter": property_price / square_meters}


@tool
def prorated_rent_calculator(
    monthly_rent: float,
    occupied_days: int,
    days_in_month: int,
) -> dict:
    """Prorate monthly rent using actual calendar days."""
    if days_in_month < 1 or not 0 <= occupied_days <= days_in_month:
        raise ValueError("occupied_days must be within days_in_month")
    daily_rent = monthly_rent / days_in_month
    return {
        "daily_rent": daily_rent,
        "prorated_rent": daily_rent * occupied_days,
    }


REAL_ESTATE_CALCULATOR_TOOLS = (
    three_x_rent_calculator,
    affo_calculator,
    arm_mortgage_calculator,
    arv_calculator,
    adr_calculator,
    biweekly_mortgage_calculator,
    biweekly_mortgage_payment_calculator,
    cap_rate_calculator,
    commercial_lease_calculator,
    down_payment_calculator,
    earnest_money_calculator,
    fha_loan_calculator,
    gift_of_equity_calculator,
    gross_rent_multiplier_calculator,
    mortgage_payoff_calculator,
    mortgage_penalty_calculator,
    mortgage_points_calculator,
    mortgage_prepayment_calculator,
    mortgage_rate_calculator,
    mortgage_refinance_calculator,
    net_effective_rent_calculator,
    net_operating_income_calculator,
    occupancy_rate_calculator,
    pag_ibig_housing_loan_calculator,
    pmi_calculator,
    price_per_square_foot_calculator,
    price_per_square_meter_calculator,
    prorated_rent_calculator,
)
