"""Presentation-specific content for the real curated review risks."""

from datetime import datetime, timezone

from app.models.risk import Risk

DATA_LIMITATIONS = [
    "SupplySentry does not store this company's supplier contracts, purchase volumes, shipment volumes, inventory cover, or customer commitments.",
    "The event establishes an external signal, not a confirmed loss or disruption for Test Electronics.",
    "Any operational or financial magnitude must be verified against internal company records before action.",
]

# Real U.S. risks retained for the presentation. Risk 396 is intentionally absent.
CURATED_US_RISK_IDS = {292, 436, 550, 724, 731, 1019, 1035, 1265, 1360, 1373, 1419}

SCENARIOS = {
292: {
"summary":"GSME and Teradyne announced a multi-year partnership to establish a semiconductor test and evaluation center in Silicon Valley. For Test Electronics, this is a High Supplier signal because Semiconductors are a configured dependency. The announcement describes expanded testing and engineering capacity; it does not establish a shortage, disruption, or direct supplier relationship with Test Electronics.",
"why":"The partnership is relevant to the semiconductor ecosystem because the new center is intended to support device evaluation, engineering development, pilot production, and production readiness. For a consumer-electronics company, changes in semiconductor testing capacity can affect supplier qualification timelines and access to production-ready components. The current evidence does not identify Test Electronics suppliers, approved test houses, allocation commitments, or component volumes.",
"next":["Map current semiconductor suppliers and identify devices dependent on external test and validation capacity.","Check qualification and production-readiness milestones for critical components.","Review supplier concentration and whether an alternative test or manufacturing partner is already qualified."],
"impact":[("Semiconductors","Procurement, Supplier Qualification, Manufacturing, Electronics Production","Potential qualification or test-capacity pressure; component lead-time pressure; supplier concentration exposure","Approved semiconductor suppliers; qualification schedules; open purchase orders; alternative test/manufacturing capacity")],
"objective":"Determine whether the new semiconductor testing capacity changes the company's supplier qualification, component availability, or lead-time exposure.",
"options":[("Monitor supplier capacity","Track affected semiconductor suppliers and qualification milestones before changing sourcing.",["Supplier capacity updates","Qualification schedules","Component lead times"]),("Protect critical components","Pre-qualify alternatives where a critical component has a single supplier or test path.",["Single-source components","Alternative supplier status","Inventory cover"]),("Escalate constrained exposure","Escalate only where internal data confirms a critical dependency and no qualified alternative exists.",["Critical BOM items","Committed production dates","Alternative qualification status"])],
"areas":["Procurement","Engineering","Operations","Supplier Management"],
"correlations":[(1035,"Both are U.S. electronics supply-chain developments involving future component or materials capacity."),(1360,"Both concern technology choices that can influence future electronics and component sourcing.")],
},
436: {
"summary":"The event reports pressure for a U.S. diesel-export restriction while fuel prices are elevated. For Test Electronics, this is a Medium Political signal with direct relevance to Diesel. The policy discussion is an external signal; it does not establish a diesel shortage or a specific company cost increase.",
"why":"Diesel affects freight carriers, distribution fleets, and other transport-intensive operations. A policy change could alter domestic fuel availability, regional price spreads, or carrier operating costs. Test Electronics' actual carrier contracts, fuel surcharges, shipment volumes, and route exposure are not stored in SupplySentry.",
"next":["Review diesel clauses and fuel-surcharge mechanisms in active carrier contracts.","Identify U.S. inbound and outbound lanes with the highest diesel-sensitive transport exposure.","Compare transport budgets with recent fuel-cost assumptions and check available modal alternatives."],
"impact":[("Diesel","Transportation, Logistics, Distribution, Fleet Operations","Fuel-cost volatility; carrier surcharge pressure; delivery-cost pressure","Carrier contracts; fuel surcharges; shipment lanes; transport budget assumptions")],
"objective":"Determine whether the diesel policy signal could materially change transportation cost or service continuity.",
"options":[("Monitor policy and fuel markets","Track policy status alongside carrier pricing rather than treating the proposal as an implemented restriction.",["Policy status","Diesel benchmark prices","Carrier notices"]),("Reduce transport exposure","Prioritize shipment consolidation and alternative modes where current contracts allow it.",["Upcoming shipments","Mode alternatives","Expedited freight exposure"]),("Escalate verified cost exposure","Escalate if contracted surcharges or fuel exposure exceed internal planning thresholds.",["Fuel-cost sensitivity","Budget variance","Critical delivery commitments"])],
"areas":["Procurement","Logistics","Finance","Operations"],
"correlations":[(550,"Both are U.S. diesel-policy signals linked to elevated fuel costs."),(731,"Both describe further development of the same U.S. diesel-export policy signal.")],
},
550: {
"summary":"The event describes the potential U.S. diesel-export restriction as a wider supply-chain issue. For Test Electronics, this is a High Political signal because Diesel is a configured dependency and North American transport costs can feed into international logistics.",
"why":"A U.S. export restriction could change where refined diesel is available and how regional fuel markets balance. For a consumer-electronics supply chain, that matters through carrier pricing, distribution, and time-sensitive delivery. The event does not show Test Electronics' actual exposure to U.S. fuel markets or any specific carrier.",
"next":["Separate U.S. domestic freight exposure from international lanes priced using U.S.-linked fuel benchmarks.","Check carrier contracts for automatic fuel-price adjustments.","Identify time-critical shipments where a fuel-cost or availability shock would materially affect delivery economics."],
"impact":[("Diesel","Transportation, Logistics, Distribution","Regional fuel-price pressure; freight-rate changes; delivery-cost volatility","Fuel surcharges; carrier rate cards; international lanes; time-critical shipments"),("North America","Regional Operations, Logistics Planning","North American transport-cost exposure; carrier availability pressure","U.S. lane volumes; carrier network; alternative routing")],
"objective":"Assess whether the U.S. fuel-policy development creates measurable transport-cost or continuity exposure for North American operations.",
"options":[("Track market transmission","Monitor diesel prices and carrier surcharges separately from the policy headline.",["Diesel benchmarks","Carrier surcharge updates","Freight quotes"]),("Protect critical lanes","Review alternative carriers and transport modes for high-priority North American shipments.",["Critical lanes","Alternative carriers","Mode capacity"]),("Escalate material exposure","Escalate when verified cost or service exposure exceeds planning thresholds.",["Budget sensitivity","Delivery commitments","Carrier alternatives"])],
"areas":["Logistics","Procurement","Finance","Operations"],
"correlations":[(436,"Both concern the same U.S. diesel-export policy development."),(731,"Both capture later stages of the diesel-export restriction discussion.")],
},
724: {
"summary":"The event describes Iran shifting trade toward land routes while maritime access and oil sales are constrained. For Test Electronics, this is a Low Political signal in the U.S.-located review set, relevant primarily through North American logistics and energy-market spillovers rather than a direct U.S. facility disruption.",
"why":"Pressure on maritime routes can redirect cargo toward land borders, creating congestion and longer transit times in affected corridors. For Test Electronics, the useful question is whether suppliers, components, or carriers use affected Middle East corridors. The current event does not identify the company's suppliers or routes.",
"next":["Check whether suppliers or inbound lanes use Gulf, Red Sea, or adjacent Middle East routing.","Review transit-time assumptions for components sourced through affected corridors.","Identify alternative ports, carriers, or sourcing regions for time-critical components."],
"impact":[("Ports","International Logistics, Import/Export, Transportation","Route disruption; transit-time pressure; freight-capacity pressure","Supplier routes; vessel bookings; port alternatives; transit-time commitments"),("North America","Regional Operations, Distribution","Potential landed-cost and inbound timing effects from global freight changes","Landed-cost assumptions; inbound schedules; carrier pricing")],
"objective":"Establish whether the Middle East trade disruption reaches any company-controlled or supplier-controlled logistics lane.",
"options":[("Monitor affected corridors","Track carrier advisories and transit-time changes before changing routes.",["Carrier notices","Transit times","Port status"]),("Prepare routing alternatives","Identify alternate ports and carriers for exposed components.",["Current routes","Alternative ports","Carrier capacity"]),("Escalate confirmed exposure","Escalate if a critical component has a route dependency with no practical alternative.",["Critical components","Route dependency","Inventory cover"])],
"areas":["Logistics","Procurement","Operations"],
"correlations":[(1265,"Both concern the U.S.-Iran/Middle East logistics situation and its effect on trade routes."),(1019,"Both are geopolitical signals in the broader U.S./Middle East supply environment.")],
},
731: {
"summary":"The event reports further support for a U.S. diesel-export restriction while fuel costs remain elevated. For Test Electronics, this is a High Political signal because Diesel is a configured dependency. It is a policy signal, not proof that an export restriction has taken effect.",
"why":"If a restriction were implemented, the relevant supply-chain channels would be diesel pricing, domestic fuel availability, carrier operating costs, and transport surcharges. The company-specific exposure is unknown because SupplySentry does not hold fuel contracts, fleet data, carrier agreements, or shipment volumes.",
"next":["Check the latest status of any proposed restriction and distinguish announced policy from implemented policy.","Review carrier fuel surcharges and transport budgets against current diesel prices.","Identify shipments that cannot readily switch between road, rail, or other transport modes."],
"impact":[("Diesel","Transportation, Logistics, Delivery Operations","Fuel-cost pressure; carrier surcharge pressure; transport continuity pressure","Diesel exposure; carrier contracts; upcoming shipments; alternative modes")],
"objective":"Verify whether the policy development creates a material transport-cost or fuel-availability exposure.",
"options":[("Verify before acting","Track implementation status and actual market pricing before changing procurement or routing.",["Policy status","Diesel prices","Carrier communications"]),("Reduce near-term exposure","Use available shipment consolidation or alternative transport capacity for exposed lanes.",["Shipment schedule","Mode alternatives","Carrier capacity"]),("Escalate material exposure","Escalate only when internal exposure is confirmed and exceeds planning thresholds.",["Cost sensitivity","Critical shipments","Budget variance"])],
"areas":["Procurement","Logistics","Finance","Operations"],
"correlations":[(436,"Same diesel-export policy signal at an earlier stage."),(550,"Same diesel-export policy signal with broader supply-chain implications.")],
},
1019: {
"summary":"The event reports a missile-interception incident involving a Saudi air-defense system. For Test Electronics, this is a High Political signal because North American operations can still be exposed indirectly through energy and logistics markets. The event does not establish a disruption to company facilities, suppliers, or shipments.",
"why":"Escalation around Middle East energy infrastructure can affect shipping routes, insurance, fuel prices, and availability of energy-related inputs. For a consumer-electronics supply chain, the relevant exposure is second-order: freight economics, energy costs, and supplier routes. No company-specific route or contract is available in the current evidence.",
"next":["Check whether critical suppliers or freight lanes transit the affected Gulf region.","Review freight and cargo-insurance changes for exposed routes.","Compare current energy and transport budgets with procurement-plan assumptions."],
"impact":[("Ports","Maritime Logistics, Import/Export, Transportation","Route and insurance pressure; shipment timing risk","Affected lanes; vessel schedules; insurance terms; alternate routes"),("Diesel","Transportation, Logistics","Fuel-cost volatility affecting carrier rates","Fuel surcharges; carrier quotes; transport budgets")],
"objective":"Determine whether regional security developments create confirmed exposure in supplier routing, freight cost, or delivery timing.",
"options":[("Monitor regional routing","Use carrier advisories and route status rather than assuming a disruption from the security event alone.",["Carrier advisories","Route status","Transit times"]),("Prepare alternate routing","Identify alternate ports or carriers for components with Middle East routing exposure.",["Critical lanes","Alternate ports","Carrier capacity"]),("Escalate verified disruption","Escalate if a critical lane is affected and internal inventory cover is insufficient.",["Inventory cover","Critical shipments","Alternative capacity"])],
"areas":["Logistics","Procurement","Risk / Compliance"],
"correlations":[(724,"Both concern the broader Middle East logistics environment."),(1265,"Both concern developments affecting Gulf trade and maritime access.")],
},
1035: {
"summary":"Nth Cycle signed a long-term recycled-minerals offtake agreement with Glencore covering lithium and other critical minerals recovered from batteries. For Test Electronics, this is a Low Supplier signal directly relevant to Lithium and Batteries. The agreement is a supply-development signal, not an immediate guarantee of component availability.",
"why":"The arrangement adds recycling capacity to the North American critical-minerals ecosystem and may broaden future sources of lithium and nickel. For Test Electronics, that is relevant to battery-material diversification and long-term sourcing resilience. The event does not show whether the company could qualify or purchase material from this supply chain.",
"next":["Track when recycled lithium and nickel products become commercially available and which customers can qualify them.","Review current battery-material supplier concentration and alternative-material qualification.","Compare recycled-material options with existing battery specifications and procurement requirements."],
"impact":[("Lithium","Procurement, Battery Supply, Supplier Management","Potential future source diversification; alternative-material availability","Qualified suppliers; material specifications; supplier concentration; future capacity"),("Batteries","Procurement, Manufacturing, Product Engineering","Potential battery-material sourcing flexibility; qualification opportunities","Battery BOMs; approved vendors; qualification timelines")],
"objective":"Assess whether emerging recycled critical-mineral capacity can become a qualified alternative to existing battery-material sources.",
"options":[("Monitor new supply","Track commercial production, product specifications, and customer qualification pathways.",["Production timeline","Material specifications","Qualification requirements"]),("Evaluate diversification","Assess whether recycled inputs could reduce concentration in the current battery-material supply base.",["Supplier concentration","Current sourcing","Alternative capacity"]),("Escalate qualification opportunity","Escalate to engineering and procurement if material is technically suitable and commercially available.",["Technical qualification","Cost comparison","Supply commitment"])],
"areas":["Procurement","Supplier Management","Engineering","Operations"],
"correlations":[(1360,"Both concern battery technology and alternatives to conventional lithium-ion supply chains."),(292,"Both are U.S. electronics supply-chain developments involving future component or materials capacity.")],
},
1265: {
"summary":"The event describes renewed diplomatic discussion around reopening the Strait of Hormuz. For Test Electronics, this is a Medium Political signal because the waterway is relevant to global energy and maritime trade. The event does not prove that shipping has normalized or that the company has a direct route dependency.",
"why":"A sustained reopening could reduce pressure on tanker and freight routes, while renewed disruption could prolong higher freight, insurance, and energy costs. For a consumer-electronics supply chain, the practical exposure is through supplier routes, component landed cost, and transport timing. Company-specific route data is not stored.",
"next":["Map supplier and carrier routes that currently use or avoid the Strait of Hormuz.","Review freight, insurance, and landed-cost assumptions for affected components.","Check inventory cover for components with limited alternative routes."],
"impact":[("Ports","Maritime Logistics, Import/Export, Transportation","Shipping-route availability; transit-time and freight-cost volatility","Vessel routes; carrier advisories; insurance; alternate ports"),("Diesel","Transportation, Logistics","Fuel-price transmission into freight costs","Fuel surcharges; freight quotes; transport budgets")],
"objective":"Use verified route and freight data to determine whether changes around Hormuz alter the company's logistics exposure.",
"options":[("Monitor route normalization","Track actual vessel movement and carrier advisories rather than relying on diplomatic announcements.",["Carrier notices","Vessel schedules","Transit times"]),("Prepare route alternatives","Maintain alternative routing for critical components where practical.",["Alternate ports","Supplier routing","Inventory cover"]),("Escalate persistent disruption","Escalate if critical lanes remain constrained and internal cover is inadequate.",["Critical shipments","Inventory cover","Alternative capacity"])],
"areas":["Logistics","Procurement","Operations","Risk / Compliance"],
"correlations":[(724,"Both concern the same Middle East trade-route disruption and potential rerouting."),(1019,"Both concern the broader regional security environment affecting maritime trade.")],
},
1360: {
"summary":"The event discusses Unigrid's sodium-ion battery technology for stationary energy storage. For Test Electronics, this is a Low Financial signal relevant to Batteries and Electricity because alternative storage chemistry could affect future component sourcing and backup-power options. Technology claims require validation before procurement decisions.",
"why":"Sodium-ion technology could broaden battery chemistry options and reduce dependence on some lithium-based inputs in suitable applications. The immediate question is whether the technology is mature, certified, cost-effective, and compatible with the company's use cases. No internal use case is stored.",
"next":["Identify whether Test Electronics has stationary-storage or backup-power use cases suitable for sodium-ion chemistry.","Check certification, cycle-life, safety, thermal, and supplier-capacity evidence.","Compare total cost and supply concentration against current battery technologies."],
"impact":[("Batteries","Procurement, Engineering, Energy Storage, Operations","Potential alternative battery sourcing; technology-qualification opportunity","Product requirements; certifications; supplier capacity; lifecycle data"),("Electricity","Energy Procurement, Operations, Backup Power","Potential backup-power resilience; storage-capacity flexibility","Power requirements; backup-power architecture; installation constraints")],
"objective":"Determine whether sodium-ion is a technically and commercially credible alternative for a company battery or backup-power requirement.",
"options":[("Monitor technology readiness","Track independently verified performance and commercial production rather than promotional claims.",["Certification","Independent performance data","Production capacity"]),("Run a qualification study","Evaluate a controlled use case if the technology meets safety and technical requirements.",["Application requirements","Safety requirements","Supplier qualification"]),("Escalate after validation","Escalate to procurement or engineering if validated performance supports diversification.",["Validated performance","Cost comparison","Supply commitment"])],
"areas":["Engineering","Procurement","Operations"],
"correlations":[(1035,"Both concern alternative battery supply and technology pathways in the U.S. market.")],
},
1373: {
"summary":"The event reports flooding in New Jersey that affected homes and triggered major storm signals. For Test Electronics, this is a Low Natural Disaster signal in the U.S. review set. The relevant supply-chain question is whether facilities, carriers, suppliers, or last-mile routes are exposed; the event alone does not establish that exposure.",
"why":"Localized flooding can interrupt road access, deliveries, employee access, warehouse operations, or utility services even when the wider network remains operational. The current evidence does not identify Test Electronics facilities, supplier sites, carrier routes, or customer locations in the affected area.",
"next":["Check whether any supplier, warehouse, customer, or carrier route is located in the affected New Jersey area.","Review upcoming deliveries and alternate road routes for exposed lanes.","Confirm business-continuity and backup-power arrangements for any exposed facility."],
"impact":[("Road","Transportation, Distribution, Last-Mile Operations","Route disruption; delivery delay; carrier availability pressure","Road-dependent routes; upcoming shipments; alternative routes; carrier status"),("Electricity","Operations, Facilities, Business Continuity","Potential facility continuity pressure if local utilities are affected","Utility status; backup power; facility continuity plans")],
"objective":"Verify whether localized flooding intersects with company or supplier activity before treating it as an operational disruption.",
"options":[("Monitor local conditions","Track official road, weather, and carrier status for affected lanes.",["Road closures","Carrier status","Delivery schedules"]),("Reroute exposed shipments","Use alternate roads or delivery windows when an affected lane is confirmed.",["Shipment priorities","Alternate routes","Carrier availability"]),("Escalate facility exposure","Escalate when a critical facility or shipment is directly affected and alternatives are limited.",["Facility status","Inventory cover","Customer commitments"])],
"areas":["Operations","Logistics","Facilities","Procurement"],
"correlations":[(1419,"Both involve U.S. logistics or energy conditions that can affect transport planning.")],
},
1419: {
"summary":"The event reports India's plan to secure U.S. LPG supplies for 2027 through a term tender. For Test Electronics, the U.S.-located signal is Low Transportation because it reflects a change in North American energy trade flows rather than a direct company disruption. The event does not establish a dependency on LPG.",
"why":"The tender indicates deliberate diversification of energy sourcing toward U.S. cargoes. For a consumer-electronics supply chain, the useful indirect question is whether changing U.S. energy flows affect freight availability, energy-market conditions, or transport costs relevant to North American operations. No such company exposure is stored.",
"next":["Monitor whether additional U.S. LPG trade changes tanker, port, or freight conditions relevant to company lanes.","Review whether North American energy-cost assumptions in transport and facility budgets need updating.","Keep this event separate from direct company fuel exposure unless internal data establishes a connection."],
"impact":[("North America","Energy Markets, Logistics Planning, Regional Operations","Potential freight and energy-market effects; changing tanker demand; regional logistics pressure","Energy-cost assumptions; relevant ports; carrier capacity; affected lanes")],
"objective":"Determine whether changing U.S. LPG trade has any measurable second-order effect on company logistics or energy costs.",
"options":[("Monitor market transmission","Watch port, tanker, and energy-market indicators without assuming direct exposure.",["Port activity","Tanker capacity","Energy prices"]),("Review planning assumptions","Check whether transport and facility budgets use materially outdated energy assumptions.",["Budget assumptions","Fuel/energy exposure","Freight rates"]),("Escalate confirmed exposure","Escalate only if internal data links the market movement to a material company exposure.",["Verified exposure","Cost sensitivity","Operational dependency"])],
"areas":["Finance","Operations","Logistics"],
"correlations":[(724,"Both involve changes in energy and maritime trade conditions affecting international logistics."),(1265,"Both concern energy-shipping conditions around major trade routes.")],
},
}

def _statement(text, ref, quote, statement_type="agent_interpretation"):
    return {"text": text, "statement_type": statement_type, "evidence_refs": [ref], "evidence_quotes": [str(quote)[:240]]}

def build_review_investigation(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    s = SCENARIOS.get(risk.id)
    if not s:
        return None
    title = event.title or "Stored event signal"
    sections = {
        "investigation_summary": [_statement(s["summary"], "E1", title, "fact")],
        "why_this_matters": [
            _statement(s["why"], "E1", title),
            _statement(f"{company_name}'s quantitative exposure remains unknown because supplier contracts, purchase volumes, shipment volumes and inventory cover are not stored.", "E3", f"{company_name} / {industry}")
        ],
        "supporting_evidence": [
            _statement(f"Stored assessment: {risk.severity or 'Unrated'} severity, {risk.risk_type or 'Unspecified'} risk type, risk score {float(risk.risk_score or 0):.2f}.", "E2", f"{risk.severity} / {risk.risk_type}"),
            _statement(f"Stored event location: {event.location or 'not specified'}; source: {event.source or 'not specified'}. These fields establish monitoring context, not company exposure.", "E1", title)
        ],
        "related_intelligence": [
            _statement(f"Risk {rid} is related because {reason}", "E1", title)
            for rid, reason in s["correlations"]
        ],
        "what_to_investigate_next": [_statement(item, "E1", title) for item in s["next"]],
    }
    return {
        "investigation_id": f"review-{risk.id}",
        "target": {"risk_id": risk.id, "event_id": event.id},
        "generated_at": datetime.now(timezone.utc),
        "model": {"provider": "curated-review", "name": "SupplySentry Review Content", "quantization": None},
        "sections": sections,
        "evidence": [
            {"ref":"E1","evidence_type":"event","label":"Stored event","data":{"id":event.id,"title":event.title,"location":event.location,"category":event.category,"source":event.source}},
            {"ref":"E2","evidence_type":"risk","label":"Stored risk assessment","data":{"id":risk.id,"severity":risk.severity,"risk_type":risk.risk_type,"risk_score":risk.risk_score}},
            {"ref":"E3","evidence_type":"company_context","label":"Company profile","data":{"company_name":company_name,"industry":industry}},
        ],
        "warnings":["Curated review content is grounded in the stored event and risk record and is decision support only."],
        "decision_support_only":True,
    }

def build_review_impact(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    s = SCENARIOS.get(risk.id)
    if not s:
        return None
    mappings = []
    for dependency, areas, impacts, checks in s["impact"]:
        direct = dependency in {"Semiconductors","Batteries","Lithium","Diesel"}
        mappings.append({
            "dependency":dependency,"category":"company_dependency","relevance":"direct" if direct else "indirect",
            "matched_terms":[dependency],"matched_on":"curated review context",
            "supply_chain_areas":[x.strip() for x in areas.split(",")],
            "potential_impacts":[x.strip() for x in impacts.split(";")],
            "verification_checks":[x.strip() for x in checks.split(";")],
        })
    relevance = "direct" if any(x["relevance"]=="direct" for x in mappings) else "indirect"
    return {
        "risk_id":risk.id,"event_id":event.id,"company_available":True,
        "company_name":company_name,"industry":industry,
        "risk":{"id":risk.id,"severity":risk.severity,"risk_type":risk.risk_type or risk.risk_name,"risk_score":risk.risk_score,"status":risk.status,"created_at":risk.created_at.isoformat() if risk.created_at else None,"prediction":None},
        "event":{"id":event.id,"title":event.title,"description":event.description,"category":event.category,"event_type":event.event_type,"location":event.location,"source":event.source},
        "relevance":relevance,"relevance_reason":f"Curated review mapping for {company_name} ({industry}).",
        "summary":f"Potential exposure areas are mapped from the event-specific review scenario. This does not claim that {company_name} has experienced these impacts.",
        "mappings":mappings,"data_limitations":DATA_LIMITATIONS,
    }

def build_review_response_plan(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    s = SCENARIOS.get(risk.id)
    if not s:
        return None
    scenario = "materials_and_supply" if any(x in {"Semiconductors","Batteries","Lithium"} for x,*_ in s["impact"]) else ("fuel_and_energy" if any(x=="Diesel" for x,*_ in s["impact"]) else ("logistics_and_transport" if any(x in {"Ports","Road","North America"} for x,*_ in s["impact"]) else "general"))
    matched = [x[0] for x in s["impact"]]
    return {
        "risk_id":risk.id,"event_id":event.id,"scenario":scenario,
        "generated_by":"curated-review","is_demo_template":False,
        "company_context_available":True,"company_name":company_name,"company_industry":industry,
        "company_relevance":"direct" if any(x in {"Semiconductors","Batteries","Lithium","Diesel"} for x in matched) else "indirect",
        "matched_dependencies":matched,"risk_summary":s["summary"],"response_objective":s["objective"],
        "immediate_checks":s["next"],
        "response_options":[{"name":n,"what_to_check":checks,"why":why,"information_required":checks} for n,why,checks in s["options"]],
        "information_required":[x for _,_,checks in s["options"] for x in checks][:8],
        "escalation_conditions":["Internal data confirms a material exposure to the event.","The affected activity is business-critical and practical alternatives are limited.","The signal persists or worsens across subsequent monitoring cycles."],
        "responsible_areas":s["areas"],"platform_recommendation":None,
        "notes":["Prepared specifically for this stored review risk.","Options are for human review; no automated business action is taken."],
        "decision_support_only":True,
    }

def build_review_correlations(db, risk_id):
    s = SCENARIOS.get(risk_id)
    if not s:
        return None
    rows = []
    for index, (rid, reason) in enumerate(s["correlations"]):
        related = db.query(Risk).filter(Risk.id == rid).first()
        if related is None or related.event is None:
            continue
        score = 78 - index * 5
        rows.append({
            "risk_id": rid,
            "event_id": related.event.id,
            "event_title": related.event.title or related.risk_name,
            "severity": related.severity,
            "risk_type": related.risk_type or related.risk_name,
            "location": related.event.location,
            "event_category": related.event.category,
            "correlation_score": score,
            "relationship_level": "high" if score >= 75 else "moderate",
            "relationship_label": "Strong relationship" if score >= 75 else "Meaningful similarity",
            "reasons": [reason],
            "shared_company_dependencies": [],
            "days_apart": None,
        })
    return {
        "risk_id": risk_id,
        "event_id": None,
        "correlations": rows[:3],
        "total_candidates_considered": len(rows),
        "analysis_window_days": 30,
        "message": None if rows else "No strongly related review signals identified.",
        "disclaimer": "Review correlations are curated relationships between displayed risk signals; they indicate relevance, not causation.",
        "company_context_available": True,
    }


def is_review_risk(risk_id: int) -> bool:
    return int(risk_id) in CURATED_US_RISK_IDS
