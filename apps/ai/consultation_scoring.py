"""
AI — Infinity Edge Consultation Scoring Algorithm
==================================================
Multi-factor point allocation engine for Track A (Homebuyer) and Track B (Investor).
Scores properties from 0 to 100 points and provides specific rationale tags.
"""
from decimal import Decimal
from typing import Any
from apps.properties.models import Property


def score_homebuyer_property(property_obj: Property, answers: dict[str, Any]) -> dict[str, Any]:
    """
    Score a property for Track A: Homebuyer (Max 100 points).
    - Budget & Financing: 30 pts
    - Location & Areas: 25 pts
    - Household & Bedrooms: 20 pts
    - Delivery Timeline: 15 pts
    - Must-haves & Amenities: 10 pts
    """
    score = 0.0
    tags = []
    reasons = []

    price = float(property_obj.price)
    budget_max = float(answers.get("budget_max") or 0.0)
    if budget_max > 0:
        if price <= budget_max:
            score += 30.0
            reasons.append("سعر العقار يقع تماماً ضمن ميزانيتك المحددة")
            tags.append("ضمن الميزانية")
        elif price <= budget_max * 1.15:
            ratio = (price - budget_max) / (budget_max * 0.15)
            score += round(30.0 * (1.0 - ratio), 1)
            reasons.append("السعر قريب جداً من ميزانيتك بمرونة طفيفة")
    else:
        score += 20.0

    # Financing match bonus
    financing_needed = answers.get("financing_needed")
    if financing_needed and financing_needed != "any":
        if property_obj.payment_method == financing_needed:
            tags.append(f"سداد {property_obj.get_payment_method_display()}")

    # 2. Location (25 pts)
    preferred_areas = answers.get("preferred_areas") or []
    if "open_to_suggestions" in preferred_areas or not preferred_areas:
        score += 22.0
        reasons.append(f"موقع متميز في {property_obj.location}")
    else:
        matched_area = next((area for area in preferred_areas if area.lower() in property_obj.location.lower()), None)
        if matched_area:
            score += 25.0
            reasons.append(f"يقع في المنطقة المفضلة لديك: {matched_area}")
            tags.append("الموقع المفضل")
        else:
            score += 8.0

    # 3. Household size & bedrooms (20 pts)
    household_size = answers.get("household_size")
    beds = property_obj.beds
    if household_size == "single_or_couple":
        if beds in (0, 1, 2):
            score += 20.0
            reasons.append(f"عدد الغرف ({beds}) مناسب تماماً لزوجين أو فرد")
        else:
            score += 10.0
    elif household_size == "small_family":
        if beds in (2, 3):
            score += 20.0
            reasons.append(f"مساحة وعدد غرف ({beds} غرف) مثالي لأسرة صغيرة")
            tags.append("مناسب لأسرة صغيرة")
        elif beds == 4:
            score += 15.0
        else:
            score += 8.0
    elif household_size == "large_family":
        if beds >= 4:
            score += 20.0
            reasons.append(f"مساحة واسعة ({beds} غرف) تلبي احتياجات الأسرة الكبيرة")
            tags.append("مناسب لأسرة كبيرة")
        elif beds == 3:
            score += 14.0
        else:
            score += 5.0
    else:
        score += 15.0

    # 4. Delivery timeline (15 pts)
    timeline = answers.get("timeline")
    if timeline == "ready":
        if property_obj.completion_status == "ready":
            score += 15.0
            reasons.append("الوحدة جاهزة للاستلام الفوري بدون انتظار")
            tags.append("استلام فوري")
        else:
            score += 5.0
    elif timeline in ("within_1_year", "within_3_years"):
        if property_obj.completion_status == "off_plan":
            score += 15.0
            reasons.append("مشروع قيد الإنشاء بفرص سداد مرنة")
            tags.append("تحت الإنشاء")
        else:
            score += 12.0
    else:
        score += 10.0

    # 5. Must-haves & amenities (10 pts)
    must_haves = answers.get("must_haves") or []
    amenity_names = [a.name.lower() for a in property_obj.amenities.all()]
    amenity_points = 0.0

    if "parking" in must_haves and property_obj.parking > 0:
        amenity_points += 3.0
        tags.append("موقف سيارات")
    if "security" in must_haves and any("أمن" in a or "حراسة" in a for a in amenity_names):
        amenity_points += 3.0
        tags.append("أمن وحراسة")
    if "pool" in must_haves and any("مسبح" in a or "سباحة" in a for a in amenity_names):
        amenity_points += 2.0
        tags.append("حمام سباحة")
    if property_obj.is_featured:
        amenity_points += 2.0

    score += min(10.0, amenity_points if must_haves else 8.0)

    # Unit type match bonus
    unit_types = answers.get("unit_types") or []
    if unit_types and property_obj.property_type in unit_types:
        tags.append(property_obj.get_property_type_display())

    final_score = min(100.0, round(score, 1))
    return {
        "score": final_score,
        "match_percentage": int(round(final_score)),
        "tags": list(dict.fromkeys(tags))[:4],
        "reasons": reasons[:3],
    }


def score_investor_property(property_obj: Property, answers: dict[str, Any]) -> dict[str, Any]:
    """
    Score a property for Track B: Investor (Max 100 points).
    - Ticket Size & Financing: 30 pts
    - Investment Goal & Risk: 25 pts
    - Asset Class & Unit Type: 20 pts
    - Hold Period & Delivery: 15 pts
    - Market Quality & Completeness: 10 pts
    """
    score = 0.0
    tags = []
    reasons = []

    price = float(property_obj.price)
    budget_max = float(answers.get("budget_max") or 0.0)

    # 1. Ticket Size & Financing (30 pts)
    if budget_max > 0:
        if price <= budget_max:
            score += 20.0
            reasons.append("سعر الوحدة متطابق مع حجم السيولة المستهدفة للاستثمار")
            tags.append("ضمن الميزانية الاستثمارية")
        elif price <= budget_max * 1.20:
            score += 15.0
    else:
        score += 18.0

    financing_pref = answers.get("financing_preference")
    if financing_pref == "cash" and property_obj.payment_method == "cash":
        score += 10.0
        tags.append("متاح خصم نقدي")
        reasons.append("سعر مميز للشراء الكاش")
    elif financing_pref == "installments" and property_obj.payment_method == "installment":
        score += 10.0
        tags.append("رافعة مالية بالتقسيط")
        reasons.append("نظام أقساط يوزع رأس المال ويعظم الرافعة المالية")
    else:
        score += 6.0

    # 2. Investment Goal & Risk (25 pts)
    goal = answers.get("investment_goal")
    risk = answers.get("risk_appetite")

    if goal == "rental_income":
        if property_obj.completion_status == "ready":
            score += 15.0
            tags.append("عائد إيجاري فوري")
            reasons.append("وحدة جاهزة للتأجير الفوري وتحقيق تدفق نقدي سريع")
        else:
            score += 8.0
    elif goal in ("capital_appreciation", "flip"):
        if property_obj.completion_status == "off_plan":
            score += 15.0
            tags.append("نمو رأسمالي واعد")
            reasons.append("شراء في مرحلة إنشائية مبكرة يضمن أقصى زيادة في القيمة السوقية")
        else:
            score += 10.0
    else:
        score += 12.0

    if risk == "established_ready" and property_obj.completion_status == "ready":
        score += 10.0
        tags.append("مخاطر منخفضة")
    elif risk == "off_plan_upside" and property_obj.completion_status == "off_plan":
        score += 10.0
        tags.append("أعلى إمكانية ربح")
    else:
        score += 6.0

    # 3. Asset Class (20 pts)
    asset_class = answers.get("preferred_asset_class")
    if asset_class == "residential":
        if property_obj.property_type in ("apartment", "duplex", "villa", "penthouse", "townhouse"):
            score += 20.0
            tags.append(property_obj.get_property_type_display())
        else:
            score += 10.0
    elif asset_class in ("retail", "admin_clinic"):
        if property_obj.property_type == "office":
            score += 20.0
            tags.append("إداري / تجاري")
        else:
            score += 8.0
    else:
        score += 15.0

    # 4. Hold Period & Timeline (15 pts)
    hold_period = answers.get("hold_period")
    if hold_period == "under_2_years":
        if property_obj.completion_status == "ready":
            score += 15.0
            reasons.append("ملائم لدورة استثمار سريعة")
        else:
            score += 8.0
    elif hold_period in ("2_to_5_years", "over_5_years"):
        score += 15.0
        reasons.append("أصل مستقر مناسب لخطة احتفاظ متوسطة إلى طويلة الأجل")
    else:
        score += 10.0

    # 5. Quality & Agent backing (10 pts)
    if property_obj.agent_id:
        score += 5.0
    if property_obj.is_featured:
        score += 5.0

    final_score = min(100.0, round(score, 1))
    return {
        "score": final_score,
        "match_percentage": int(round(final_score)),
        "tags": list(dict.fromkeys(tags))[:4],
        "reasons": reasons[:3],
    }


def score_property_for_track(property_obj: Property, track: str, answers: dict[str, Any]) -> dict[str, Any]:
    """
    Score property based on the consultation track.
    """
    if track == "investor":
        return score_investor_property(property_obj, answers)
    return score_homebuyer_property(property_obj, answers)
