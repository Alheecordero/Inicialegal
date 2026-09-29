"""Separa lo común de los planes y lo que cambia el precio."""


def build_plan_offer(plans):
    plans = list(plans)
    grouped = {}
    order = []
    for plan in plans:
        for feature in plan.features.all():
            if feature.title not in grouped:
                grouped[feature.title] = []
                order.append(feature.title)
            grouped[feature.title].append(feature)

    count = len(plans)
    shared = []
    differing = []
    for title in order:
        items = grouped[title]
        texts = {item.text for item in items}
        if count > 1 and len(items) == count and len(texts) == 1:
            shared.append(items[0])
        else:
            differing.append(title)

    priced = [plan for plan in plans if plan.price_annual is not None]
    base = None
    if len(priced) >= 2 and len({plan.currency for plan in priced}) == 1:
        base = min(priced, key=lambda plan: plan.price_annual)

    for plan in plans:
        plan.offer_features = [feature for feature in plan.features.all() if feature.title in differing]
        plan.price_more = None
        plan.price_base_name = ""
        if base and plan.pk != base.pk and plan.price_annual is not None and plan.currency == base.currency:
            plan.price_more = plan.price_annual - base.price_annual
            plan.price_base_name = base.name

    return {
        "plans": plans,
        "shared_features": shared,
        "has_difference": bool(differing) and count > 1,
    }
