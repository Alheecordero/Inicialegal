"""Inglés de las fichas comerciales.

Solo completa un campo en inglés si está vacío. Una edición hecha en el
panel, o una nueva ejecución del seed, no borra la traducción.
Las páginas legales y los artículos del blog no se traducen aquí.
"""
from apps.blog.models import Category
from apps.core.models import FAQ, HeroSlide, Plan, PlanBenefit, PlanFeature, PracticeArea, Service, SiteSettings, TeamMember


def _blank(value):
    return value is None or not str(value).strip()


def _needs_english(obj, name):
    """Vacío, o todavía el valor por defecto del campo (no es una traducción)."""
    attr = f"{name}_en"
    if not hasattr(obj, attr):
        return False
    value = getattr(obj, attr)
    if _blank(value):
        return True
    field = obj._meta.get_field(name)
    default = field.default
    if default is None or callable(default):
        return False
    return value == default


def _fill(obj, **fields):
    changed = False
    for name, value in fields.items():
        if not _needs_english(obj, name):
            continue
        setattr(obj, f"{name}_en", value)
        changed = True
    if changed:
        obj.save()
    return changed


def _clear_copied_english(model, fields):
    """Vacía el inglés que solo repite el español. Así no se anuncia como traducción."""
    n = 0
    for obj in model.objects.all():
        changed = False
        for name in fields:
            attr = f"{name}_en"
            if not hasattr(obj, attr):
                continue
            english = getattr(obj, attr) or ""
            spanish = getattr(obj, name) or ""
            if english and english == spanish:
                setattr(obj, attr, "")
                changed = True
        if changed:
            obj.save()
            n += 1
    return n


def apply_english(stdout=None):
    from apps.blog.models import Post
    from apps.core.models import Page

    n = 0
    n += _clear_copied_english(Page, ("title", "subtitle", "content", "meta_description"))
    n += _clear_copied_english(Post, ("title", "excerpt", "content", "meta_title", "meta_description", "cover_caption"))
    n += _settings()
    n += _areas()
    n += _services()
    n += _plans()
    n += _team()
    n += _hero()
    n += _faqs()
    n += _categories()
    if stdout is not None:
        stdout.write(f"· Inglés comercial ({n} fichas actualizadas, sin pisar traducciones existentes)")
    return n


def _settings():
    site = SiteSettings.load()
    return int(_fill(
        site,
        tagline="Corporate law firm",
        schedule="Monday to Friday, 9:00 a.m. to 6:00 p.m.",
        whatsapp_message="Hello, I would like further information about Inicia Legal's services.",
        about_kicker="The firm",
        about_title="Legal judgment for the company's decisions",
        about_text=(
            "<p>Inicia Legal is a corporate law firm that advises growing companies "
            "on the matters that shape their operations: corporate and contract law, labour law, tax law, "
            "economic criminal law and compliance, data protection, cybersecurity, and industrial property.</p>"
            "<p>Our practice rests on one principle: a company's legal contingencies are handled "
            "more effectively before they arise. We therefore advise our clients on an ongoing basis "
            "in the conclusion of their contracts, the management of their employment relationships, their corporate "
            "structure and their regulatory compliance.</p>"
            "<p>Each matter is conducted by lawyers specialised in the relevant area, with the technical rigour "
            "of a large firm and a close understanding of each client's company.</p>"
        ),
        cta_title="Request a meeting",
        cta_text="The first meeting is free of charge.",
        cta_button_text="Request a meeting",
        footer_text=(
            "Corporate law firm. We advise companies on corporate law, labour law, "
            "tax law, economic criminal law and compliance."
        ),
        meta_description=(
            "Corporate law firm in Las Condes. Advice to companies on corporate law, "
            "labour law, tax law, economic criminal law and compliance."
        ),
        cookie_consent_title="Manage consent",
        cookie_consent_text=(
            "This website uses cookies and other technologies, and processes the personal data you provide in order to "
            "offer a better experience, respond to your requests and fulfil the purposes described in our Privacy "
            "Policy, in accordance with Law No. 21,719 on the Protection of Personal Data. You may accept, "
            "refuse or set your preferences at any time."
        ),
    ))


def _areas():
    copy = {
        "corporativo": (
            "Corporate",
            "Corporate law, contracts and due diligence for the company's operations.",
            "<p>The corporate group covers company law, contracts and the legal audit "
            "of an investment or a sale and purchase.</p>"
            "<h3>Areas</h3><ul><li>Company law</li><li>Civil law and contracts</li><li>Due diligence</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Incorporation and amendment of companies</li>"
            "<li>Shareholders' agreements</li>"
            "<li>Commercial contracts</li>"
            "<li>Legal audit for investment and sale-and-purchase processes</li></ul>"
            "<p>Civil litigation, judicial collection and defence before SERNAC are handled in this group.</p>",
        ),
        "derecho-laboral": (
            "Labour law",
            "Internal regulations, working hours, labour audits and labour litigation.",
            "<p>We advise the company on labour compliance and on the defence of its contingencies.</p>"
            "<h3>Areas</h3><ul><li>Labour law</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Internal regulations with the protocol required by Law No. 21,643</li>"
            "<li>Adjustment of working hours to Law No. 21,561</li>"
            "<li>Overtime agreements</li>"
            "<li>Labour audit</li>"
            "<li>Labour litigation</li></ul>",
        ),
        "derecho-tributario": (
            "Tax law",
            "Planning, restructurings and regularisations before the Chilean Internal Revenue Service.",
            "<p>We guide the company's decisions when they have a tax effect, and in its dealings "
            "with the Chilean Internal Revenue Service (Servicio de Impuestos Internos).</p>"
            "<h3>Areas</h3><ul><li>Tax law</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Tax planning</li>"
            "<li>Restructurings with a tax effect</li>"
            "<li>Regularisations before the Chilean Internal Revenue Service</li>"
            "<li>Regularisation of undeclared foreign-source income in Chile (2025, 2024 and 2023, not time-barred)</li>"
            "<li>Defence in respect of notices, summonses and audits by the Chilean Internal Revenue Service</li>"
            "<li>Tax due diligence</li></ul>",
        ),
        "derecho-penal-economico": (
            "Economic criminal law and compliance",
            "Crime-prevention models, compliance programmes and internal investigations.",
            "<p>We prevent and analyse the criminal liability of the legal entity and of its management.</p>"
            "<h3>Areas</h3><ul><li>Economic criminal law</li><li>Crime-prevention models</li><li>Compliance</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Prevention models under Laws No. 20,393 and No. 21,595</li>"
            "<li>Compliance programmes</li>"
            "<li>Internal investigations</li>"
            "<li>Whistleblowing channel</li></ul>",
        ),
        "tecnologia-y-datos": (
            "Technology and data",
            "Personal-data protection and cybersecurity for the company.",
            "<p>We advise the company on the personal-data regime and on the contracts for its technology operations.</p>"
            "<h3>Areas</h3><ul><li>Personal-data protection</li><li>Cybersecurity</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Alignment with Law No. 21,719</li>"
            "<li>Privacy policies and terms and conditions</li>"
            "<li>Technology contracts</li>"
            "<li>Compliance with Law No. 21,663</li>"
            "<li>Cybersecurity framework</li></ul>",
        ),
        "propiedad-industrial": (
            "Industrial property",
            "Registration and defence of trade marks and patents.",
            "<p>We protect the company's distinctive signs before the Chilean National Institute of Industrial Property "
            "and the Industrial Property Court.</p>"
            "<h3>Areas</h3><ul><li>Trade marks</li><li>Patents</li></ul>"
            "<h3>Representative services</h3><ul>"
            "<li>Trade mark registration before the Chilean National Institute of Industrial Property</li>"
            "<li>Oppositions</li>"
            "<li>Defence and appeals before the Industrial Property Court</li></ul>",
        ),
    }
    n = 0
    for slug, (name, short, desc) in copy.items():
        obj = PracticeArea.objects.filter(slug=slug).first()
        if obj and _fill(obj, name=name, short_description=short, description=desc):
            n += 1
    return n


def _services():
    copy = {
        "Revisión de contratos": (
            "Contract review",
            "Review of contracts before signature, to identify risks, unfair clauses and gaps.",
            "Included in Plan Legal Pyme and Plan Legal Advance",
        ),
        "Confección de contratos": (
            "Contract drafting",
            "Contracts designed for the company: clients, suppliers, services and confidentiality.",
            "Included in the annual plans",
        ),
        "Asesoría legal continua": (
            "Ongoing legal advice",
            "Ordinary legal queries handled by a specialised team, throughout the year.",
            "Included in Plan Legal Pyme and Plan Legal Advance",
        ),
        "Defensa ante reclamos SERNAC": (
            "Defence of SERNAC claims",
            "Management and defence of consumer claims processed before SERNAC.",
            "On request",
        ),
        "Representación en juicios civiles": (
            "Representation in civil proceedings",
            "Judicial representation of the company in civil and commercial matters.",
            "On request",
        ),
        "Mediaciones, conciliaciones y negociaciones": (
            "Mediation, conciliation and negotiation",
            "Legal support in mediation, conciliation and negotiation with third parties.",
            "On request",
        ),
        "Cumplimiento laboral": (
            "Labour compliance",
            "Employment contracts, addenda, internal regulations, dismissals and responses to labour inspections.",
            "On request",
        ),
        "Constitución y modificación de sociedades": (
            "Incorporation and amendment of companies",
            "Company formation, corporate amendments, shareholders' agreements and reorganisations.",
            "On request",
        ),
        "Protección de marca": (
            "Trade mark protection",
            "Registration and defence of trade marks before INAPI in order to protect the company's identity.",
            "On request",
        ),
        "Orientación tributaria": (
            "Tax guidance",
            "Legal advice on tax matters connected with the company's operations and structure.",
            "On request",
        ),
        "Regularización de rentas de fuente extranjera": (
            "Regularisation of foreign-source income",
            "Regularisation before the Chilean Internal Revenue Service of foreign-source income not declared in Chile during 2025, 2024 and 2023, years that are not time-barred.",
            "On request",
        ),
        "Defensa tributaria ante el SII": (
            "Tax defence before the Chilean Internal Revenue Service",
            "Defence of the company in respect of notices, summonses and any audit by the Chilean Internal Revenue Service.",
            "On request",
        ),
        "Prevención de delitos económicos": (
            "Prevention of economic crime",
            "Prevention models and analysis of corporate criminal-liability risks.",
            "On request",
        ),
    }
    n = 0
    for spanish, (name, short, note) in copy.items():
        obj = Service.objects.filter(name=spanish).first()
        if obj is None:
            continue
        desc = f"<p>{short}</p><p>Please request a meeting to receive a proposal suited to the company.</p>"
        if _fill(obj, name=name, short_description=short, description=desc, price_note=note):
            n += 1
    return n


def _plans():
    tagline = "Ongoing legal support for companies that wish to operate with security, order and legal prevention."
    summary = (
        "An annual legal service so that the company has permanent legal support, "
        "preventive advice and strategic guidance on its most important decisions."
    )
    problem_title = "Many SMEs make legal decisions only once the problem has already begun."
    problem_text = (
        "Contracts signed without review, labour breaches, lack of trade mark protection, disputes "
        "with clients or suppliers, and legal queries answered too late can generate costs, fines, claims "
        "and loss of management time.\n\nThe risk is not always visible at the outset, but it appears once the company is already exposed."
    )
    benefits = {
        "Respaldo durante todo el año": (
            "Support throughout the year",
            "It avoids the uncertainty of instructing lawyers for each query or document.",
        ),
        "Prevención de riesgos": (
            "Risk prevention",
            "It makes it possible to identify and correct problems before they escalate.",
        ),
        "Mejores decisiones empresariales": (
            "Better company decisions",
            "Access to legal guidance before signing, hiring, dismissing or negotiating.",
        ),
        "Orden legal permanente": (
            "Ongoing legal order",
            "Contracts, labour compliance, trade marks and documents under professional review.",
        ),
        "Acompañamiento especializado": (
            "Specialised support",
            "A legal team available in the company's principal critical areas.",
        ),
    }
    features = {
        "Equipo jurídico especializado": (
            "Specialised legal team",
            "Access to a team in corporate, labour, tax, economic criminal law and compliance, data and industrial property matters.",
        ),
        "Asesorías legales": (
            "Legal advice",
            "Ordinary queries during the term of the plan.",
        ),
        "Confección de contratos": (
            "Contract drafting",
            None,
        ),
        "Auditoría laboral": (
            "Labour audit",
            "2 audits a year, one each semester.",
        ),
        "Revisión de contratos": (
            "Contract review",
            "Up to 3 contracts a month.",
        ),
        "Cobranza judicial": (
            "Judicial collection",
            "Judicial collection of invoices, cheques and promissory notes.",
        ),
        "Juicio laboral": (
            "Labour proceedings",
            "Ordinary or summary labour proceedings.",
        ),
    }
    drafting = {
        "plan-legal-pyme": "2 contracts a year, designed for the company.",
        "plan-legal-advance": "4 contracts a year, designed for the company.",
    }
    n = 0
    for plan in Plan.objects.filter(slug__in=["plan-legal-pyme", "plan-legal-advance"]):
        if _fill(
            plan,
            tagline=tagline,
            summary=summary,
            problem_title=problem_title,
            problem_text=problem_text,
            solution_title=f"{plan.name} by Inicia Legal",
            solution_text=(
                f"With {plan.name}, the company stops reacting to legal contingencies and begins to "
                "prevent them with professional support throughout the year."
            ),
            price_note="Payment methods: bank transfer, debit card or credit card.",
            discount_badge="Up to 15% off additional services",
            discount_text=(
                f"By retaining {plan.name}, the company obtains a preferential fee for additional legal services "
                "that are not included in the plan. This benefit applies to Inicia Legal's professional fees, "
                "subject to an assessment and a quotation for the service required."
            ),
            cta_text="Request this plan",
        ):
            n += 1
        for feature in plan.features.all():
            pair = features.get(feature.title)
            if not pair:
                continue
            title, text = pair
            if feature.title == "Confección de contratos":
                text = drafting.get(plan.slug, text)
            if _fill(feature, title=title, text=text):
                n += 1
        for benefit in plan.benefits.all():
            pair = benefits.get(benefit.title)
            if pair and _fill(benefit, title=pair[0], text=pair[1]):
                n += 1
    return n


def _team():
    copy = {
        "angela-montiel": (
            "Founding partner",
            "Corporate lawyer",
            "<p><strong>Ángela María Montiel Báez</strong> is a corporate lawyer and founding partner of Inicia Legal. "
            "She advises companies and SMEs on the structure of their contractual relationships, the prevention of "
            "disputes and decision-making with legal support.</p>"
            "<h3>Education</h3><ul>"
            "<li>Attorney.</li>"
            "<li>Diploma in Public Procurement, Universidad de Chile (2023).</li>"
            "<li>Diploma in Civil Liability, Universidad de Chile (2024).</li>"
            "<li>Diploma in Corporate Taxation, Universidad Andrés Bello (2026).</li>"
            "</ul>"
            "<h3>Areas of practice</h3><p>Company law, civil contracting, public procurement, civil liability and corporate taxation.</p>",
        ),
        "natalia-acuna": (
            "Founding partner",
            "Criminal lawyer",
            "<p><strong>Natalia Acuña Illanes</strong> is a criminal lawyer and founding partner of Inicia Legal. "
            "She specialises in the prevention and analysis of risks associated with economic crime and with the "
            "criminal liability of companies, as well as in environmental compliance.</p>"
            "<h3>Education</h3><ul>"
            "<li>Attorney.</li>"
            "<li>Diploma in Economic Criminal Law, Pontificia Universidad Católica de Chile (2021).</li>"
            "<li>Diploma in Environmental Law – Environmental Management Instruments, Universidad de Chile (2023).</li>"
            "</ul>"
            "<h3>Areas of practice</h3><p>Economic criminal law, criminal liability of legal entities, compliance and environmental law.</p>",
        ),
        "juan-gallardo": (
            "Lawyer",
            "Specialist in labour law",
            "<p><strong>Juan Gallardo Vera</strong> is a lawyer specialising in labour law.</p>"
            "<h3>Education</h3><ul>"
            "<li>Attorney, Universidad Central de Chile.</li>"
            "<li>Personnel Administrator, Universidad de Santiago de Chile.</li>"
            "<li>Diploma in Corporate Social Responsibility, Universidad Alberto Hurtado (2010).</li>"
            "</ul>"
            "<h3>Areas of practice</h3><p>Labour law.</p>",
        ),
        "fadwa-saba": (
            "Lawyer",
            "Specialist in criminal law",
            "<p><strong>Fadwa Saba</strong> is a lawyer specialising in criminal law. "
            "She practised for more than 10 years as a Public Criminal Defender in the Metropolitan Region. "
            "She specialises in violent offences, Law 20,000, the Firearms Act, the Traffic Act, domestic violence, and offences against persons and property.</p>"
            "<h3>Education</h3><ul>"
            "<li>Attorney.</li>"
            "<li>Master's degree in Criminal Law and Criminal Sciences, Universidad de Sevilla, Spain (2023).</li>"
            "<li>Master's degree in Criminal Law and Constitutional Guarantees, Universidad de Jaén, Spain (2018).</li>"
            "<li>Diploma in Equality and Non-discrimination, Universidad de Buenos Aires, Argentina (2022).</li>"
            "<li>Diploma in Criminal Analysis for Security Management, Universidad Alberto Hurtado (2022).</li>"
            "<li>Diploma in Economic Criminal Law, Universidad Católica de Chile (2021).</li>"
            "<li>Diploma in Constitutional Guarantees, Universidad de Jaén, Spain (2019).</li>"
            "</ul>"
            "<h3>Areas of practice</h3><p>Violent offences, Law 20,000, the Firearms Act, the Traffic Act, domestic violence, and offences against persons and property.</p>",
        ),
    }
    n = 0
    for slug, (role, specialty, bio) in copy.items():
        obj = TeamMember.objects.filter(slug=slug).first()
        if obj and _fill(obj, role=role, specialty=specialty, bio=bio):
            n += 1
    return n


def _hero():
    copy = {
        "principal": (
            "Corporate law firm",
            "Legal rigour. *A company's perspective.*",
            "Specialised advice in company law, labour law, tax law, economic criminal law and compliance, data protection and industrial property.",
            "See our practice areas",
        ),
        "banners": (
            "Publications",
            "What you should know *before you sign*",
            "Practical articles on contracts, labour law, tax law, economic criminal law and industrial property.",
            "View the publications",
        ),
        "planes": (
            "Ongoing advice",
            "Annual *support*",
            "Legal advisory plans for companies.",
            "See our plans",
        ),
    }
    n = 0
    for key, (kicker, title, subtitle, primary) in copy.items():
        obj = HeroSlide.objects.filter(key=key).first()
        if obj and _fill(obj, kicker=kicker, title=title, subtitle=subtitle, primary_text=primary):
            n += 1
    return n


def _faqs():
    general = {
        "¿A quién asesora Inicia Legal?": (
            "Whom does Inicia Legal advise?",
            "Inicia Legal advises companies, their partners and their managers. Criminal matters of natural persons are handled by Abogadas Penalistas, a related firm specialised in criminal defence.",
        ),
        "¿La primera reunión tiene costo?": (
            "Does the first meeting have a fee?",
            "No. The initial meeting is free of charge and allows the firm to understand the company's legal situation.",
        ),
        "¿Atienden de forma remota?": (
            "Do you work remotely?",
            "Yes. The firm works both in person and remotely, with video meetings and digital document management.",
        ),
        "¿Cómo puedo contactarlos?": (
            "How may I contact you?",
            "You may write through the form, by email, by telephone or by WhatsApp. We reply promptly during business hours.",
        ),
    }
    shared = {
        "¿Cuál es la duración del plan?": (
            "What is the term of the plan?",
            "The plan has a term of one year and may be paid in up to 12 instalments.",
        ),
        "¿Qué pasa si necesito un servicio que no está incluido?": (
            "What if I need a service that is not included?",
            "As a client of the plan, your company has access to a preferential fee of up to 15% off Inicia Legal's professional fees, subject to an assessment and a quotation.",
        ),
        "¿Cómo se activa el plan?": (
            "How is the plan activated?",
            "The payment method is confirmed and the initial meeting is arranged. From that moment the company has ongoing legal support.",
        ),
    }
    includes = {
        "plan-legal-pyme": (
            "It includes a specialised legal team, ordinary queries during the term, 2 tailored contracts a year, "
            "2 labour audits a year, review of up to 3 contracts a month, and judicial collection of invoices, cheques and promissory notes."
        ),
        "plan-legal-advance": (
            "It includes a specialised legal team, ordinary queries during the term, 4 tailored contracts a year, "
            "2 labour audits a year, review of up to 3 contracts a month, judicial collection of invoices, cheques and promissory notes, "
            "and ordinary or summary labour proceedings."
        ),
    }
    n = 0
    for faq in FAQ.objects.filter(plan=None):
        pair = general.get(faq.question)
        if pair and _fill(faq, question=pair[0], answer=pair[1]):
            n += 1
    for faq in FAQ.objects.exclude(plan=None).select_related("plan"):
        if faq.question.startswith("¿Qué incluye"):
            text = includes.get(faq.plan.slug)
            if text and _fill(faq, question=f"What does {faq.plan.name} include?", answer=text):
                n += 1
            continue
        pair = shared.get(faq.question)
        if pair and _fill(faq, question=pair[0], answer=pair[1]):
            n += 1
    return n


def _categories():
    names = {
        "Societario": "Corporate",
        "Laboral": "Labour",
        "Tributario": "Tax",
        "Penal económico": "Economic criminal law",
        "Tecnología y datos": "Technology and data",
        "Propiedad industrial": "Industrial property",
    }
    n = 0
    for spanish, english in names.items():
        obj = Category.objects.filter(name=spanish).first()
        if obj and _fill(obj, name=english):
            n += 1
    return n
