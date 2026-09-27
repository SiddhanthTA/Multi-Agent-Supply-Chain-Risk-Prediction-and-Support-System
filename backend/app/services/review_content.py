"""Presentation-specific content for the real curated review risks."""

from datetime import datetime, timezone

from app.models.risk import Risk
from app.models.review_risk import ReviewRisk

DATA_LIMITATIONS = [
    "SupplySentry does not store this company's supplier contracts, purchase volumes, shipment volumes, inventory cover, or customer commitments.",
    "The event establishes an external signal, not a confirmed loss or disruption for Test Electronics.",
    "Any operational or financial magnitude must be verified against internal company records before action.",
]

# Real U.S. risks retained for the presentation. Risk 396 is intentionally absent.
CURATED_US_RISK_IDS = {292, 101, 1035, 1265, 1360, 1373}
CURATED_INDIA_RISK_IDS = {701, 224, 95, 1131}
CURATED_GLOBAL_RISK_IDS = {391, 109, 724}
CURATED_REVIEW_RISK_IDS = CURATED_US_RISK_IDS | CURATED_INDIA_RISK_IDS | CURATED_GLOBAL_RISK_IDS
# Existing stored risks selected for the India/global review workspaces.
# These IDs are only surfaced in the presentation layer; underlying records are unchanged.
CURATED_INDIA_RISK_IDS = {701, 224, 715, 95, 1131}
CURATED_GLOBAL_RISK_IDS = {391, 109, 101}
CURATED_REVIEW_RISK_IDS = CURATED_US_RISK_IDS | CURATED_INDIA_RISK_IDS | CURATED_GLOBAL_RISK_IDS

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

SCENARIOS.update({
701: {
"summary":"Nexperia and Tata Electronics announced a strategic partnership covering semiconductor manufacturing, assembly and testing in India. For Test Electronics, this is a High Supplier signal directly relevant to Semiconductors. It represents potential ecosystem diversification and local capacity development, not a confirmed improvement in the company's own component supply.",
"why":"Nexperia supplies chips used in consumer electronics, and the partnership adds Indian manufacturing, packaging and testing capacity. For Test Electronics, the useful question is whether existing or future semiconductor sourcing can use this ecosystem and whether qualification paths become more diverse. The current evidence does not identify the company's Nexperia exposure or approved suppliers.",
"next":["Map semiconductor BOM items and identify any Nexperia or equivalent power-control components.","Review supplier concentration and qualification requirements for components that could use Indian assembly/test capacity.","Track Dholera and Jagiroad production/qualification milestones before treating the new capacity as available supply."],
"impact":[("Semiconductors","Procurement, Supplier Qualification, Manufacturing","Potential sourcing diversification; future qualification capacity; reduced single-region concentration if qualified","Approved suppliers; component BOMs; qualification timelines; production milestones")],
"objective":"Determine whether India's expanding semiconductor ecosystem can create a qualified alternative or resilience path for critical components.",
"options":[("Monitor capacity build-out","Track manufacturing, packaging and testing milestones before changing sourcing.",["Production milestones","Qualification status","Supplier capacity"]),("Evaluate alternative sourcing","Identify components that could qualify through Indian semiconductor manufacturing or test partners.",["BOM exposure","Alternate suppliers","Technical qualification"]),("Escalate qualification opportunity","Escalate where a critical component has high concentration and a credible alternative becomes available.",["Single-source exposure","Qualification lead time","Supply commitment"])],
"areas":["Procurement","Engineering","Supplier Management","Operations"],"correlations":[(224,"Both concern India's battery/semiconductor supply-chain ecosystem and local sourcing development."),(1131,"Both concern India's longer-term shift in technology and energy infrastructure relevant to electronics.")]},
224: {
"summary":"E3 Lithium signed a non-binding memorandum to potentially supply battery-grade lithium carbonate to India's Epsilon CAM. For Test Electronics, this is a Medium Supplier signal directly relevant to Lithium and Batteries. The MoU is a potential future supply arrangement, not a committed source for Test Electronics.",
"why":"A new lithium-carbonate supply pathway into India could diversify battery-material sourcing and reduce concentration in established supply routes if it reaches production and qualification. Test Electronics' battery suppliers, material specifications and purchase volumes are not stored.",
"next":["Review battery material supplier concentration and geographic exposure.","Track the Clearwater project's production and qualification milestones.","Identify whether future battery suppliers could qualify material from this route."],
"impact":[("Lithium","Battery Procurement, Supplier Management, Manufacturing","Potential material-source diversification; future lithium availability; qualification opportunity","Material specifications; approved suppliers; production capacity; qualification schedule"),("Batteries","Product Engineering, Manufacturing, Procurement","Potential diversification of battery-material inputs","Battery BOMs; cell suppliers; chemistry requirements")],
"objective":"Assess whether the emerging Canada-to-India lithium supply route could become a credible qualified source for battery materials.",
"options":[("Monitor project progress","Track commercial production, quality specifications and delivery readiness.",["Production timeline","Material quality","Delivery capability"]),("Evaluate diversification","Assess whether the route could reduce current lithium supplier concentration.",["Supplier concentration","Current contracts","Alternative capacity"]),("Escalate qualification","Begin supplier qualification only when commercial material and technical documentation are available.",["Samples","Certification","Commercial terms"])],
"areas":["Procurement","Supplier Management","Engineering","Operations"],"correlations":[(701,"Both concern development of alternative supply capacity for India's electronics and battery ecosystem."),(95,"Both concern Indian industrial inputs and energy/material availability.")]},
715: {
"summary":"India's growth outlook was raised while El Nino-related food and inflation risks remained a concern. For Test Electronics, this is a Medium Financial signal because demand conditions and input-cost pressure can influence electronics planning. It does not establish a company-specific demand change.",
"why":"Changes in Indian growth and food/energy conditions can affect consumer demand, operating costs and working-capital planning. The company-specific sales exposure, inventory levels and supplier costs are not stored.",
"next":["Review India demand assumptions for consumer-electronics products.","Check whether energy, logistics or imported-input costs have moved against the operating plan.","Monitor agricultural and energy conditions that could affect consumer spending or input inflation."],
"impact":[("Electricity","Operations, Cost Planning","Potential operating-cost pressure from energy conditions","Energy budget; facility consumption; tariff exposure")],
"objective":"Check whether the revised India macro outlook changes demand or cost assumptions used in supply-chain planning.",
"options":[("Monitor demand indicators","Track consumer demand and input-cost data alongside the growth forecast.",["Orders","Demand forecasts","Input costs"]),("Refresh planning assumptions","Update scenario assumptions if demand or costs materially diverge.",["Budget variance","Inventory plan","Demand forecast"]),("Escalate material deviation","Escalate only where verified demand/cost changes affect supply commitments.",["Customer orders","Inventory exposure","Supplier commitments"])],
"areas":["Finance","Sales Planning","Operations","Procurement"],"correlations":[(95,"Both reflect Indian industrial and energy conditions affecting planning assumptions."),(1131,"Both concern structural changes in India's economy and energy use.")]},
95: {
"summary":"India's August core-sector growth slowed to 4.8% as coal, crude oil, natural gas and fertilizer output weakened while electricity and cement remained stronger. For Test Electronics, this is a Medium Financial signal relevant to Electricity and Coal because industrial input conditions can affect operating costs and supplier activity.",
"why":"The mixed sector data matters because energy and industrial inputs sit upstream of manufacturing and logistics. A slowdown in coal or gas output can tighten energy conditions even when electricity generation remains strong. Test Electronics' facility energy contracts and supplier exposure are not stored.",
"next":["Review electricity and energy procurement assumptions for Indian operations.","Identify suppliers dependent on coal, gas or fertilizer-intensive industrial inputs.","Track whether the weakness persists for more than one reporting period."],
"impact":[("Electricity","Facilities, Manufacturing, Operations","Potential energy-cost or availability pressure if weakness persists","Power contracts; consumption; tariff changes"),("Coal","Industrial Supplier Network, Energy","Potential upstream input pressure for energy-intensive suppliers","Supplier energy exposure; production capacity; lead times")],
"objective":"Determine whether Indian core-sector weakness is translating into a measurable supply or operating-cost exposure.",
"options":[("Monitor sector data","Track the next core-sector releases and energy indicators.",["Coal output","Gas output","Electricity generation"]),("Review supplier exposure","Identify suppliers whose production depends on affected industrial inputs.",["Supplier map","Production capacity","Lead times"]),("Escalate persistent pressure","Escalate only if supplier or facility data confirms material exposure.",["Supplier disruption","Cost variance","Inventory cover"])],
"areas":["Operations","Procurement","Finance","Supplier Management"],"correlations":[(1131,"Both concern India's evolving electricity and energy system."),(701,"Both affect the wider Indian manufacturing ecosystem relevant to electronics supply.")]},
1131: {
"summary":"An IEA outlook indicates India's electrification rate could rise substantially by 2035, with transport electrification a major contributor. For Test Electronics, this is a Low Financial signal relevant to Electricity and Batteries because it points to a long-term shift in energy and transport demand rather than an immediate disruption.",
"why":"Greater electrification can change demand for batteries, power electronics, charging infrastructure and electricity capacity. It may also reduce some fuel dependence over time. The company's product roadmap and exposure to these markets are not stored.",
"next":["Identify products or components exposed to electrification and power-electronics demand.","Review battery and power-electronics supplier capacity for long-term planning.","Assess whether transport electrification changes the company's logistics or energy assumptions."],
"impact":[("Electricity","Product Planning, Facilities, Energy Procurement","Long-term power demand and infrastructure considerations","Power requirements; energy plans; grid exposure"),("Batteries","Product Engineering, Procurement","Potential growth in battery-related demand and sourcing requirements","Battery roadmap; cell supply; qualification capacity")],
"objective":"Translate the long-term electrification trend into concrete product, battery and energy planning questions.",
"options":[("Monitor market transition","Track electrification adoption and supplier capacity.",["Market adoption","Supplier capacity","Technology roadmap"]),("Evaluate strategic exposure","Map products and components that could benefit from or be constrained by the transition.",["Product portfolio","Battery BOMs","Power-electronics exposure"]),("Escalate planning change","Escalate when verified demand or supplier constraints warrant a roadmap adjustment.",["Demand forecast","Capacity commitments","Supplier qualification"])],
"areas":["Product Engineering","Procurement","Operations","Strategy"],"correlations":[(224,"Both concern battery-material and energy-transition supply development."),(701,"Both concern structural changes in India's electronics supply ecosystem.")]},
391: {
"summary":"Crude prices rose as U.S.-Iran negotiations remained unresolved and oil flows through the Strait of Hormuz faced continued uncertainty. For Test Electronics, this is a High Financial signal because global energy prices can transmit into transport, manufacturing and logistics costs. It does not establish a direct company loss.",
"why":"Crude-price volatility can feed diesel, marine fuel, freight rates and energy costs across global supply chains. The company-specific sensitivity depends on carrier contracts, energy procurement and shipment volume, none of which are stored.",
"next":["Review fuel and freight assumptions in current budgets.","Check carrier fuel-surcharge exposure and major ocean/road lanes.","Identify energy-intensive suppliers and time-critical shipments vulnerable to freight-cost changes."],
"impact":[("Diesel","Transportation, Logistics","Fuel and freight-cost volatility","Carrier surcharges; transport budget; shipment lanes"),("Ports","International Logistics, Import/Export","Freight and route-cost pressure","Port routes; freight quotes; transit times")],
"objective":"Determine how much of the company's logistics and operating cost base is sensitive to global energy-price volatility.",
"options":[("Monitor energy markets","Track crude, diesel and freight indicators together.",["Crude benchmarks","Diesel prices","Freight rates"]),("Reduce exposure","Consolidate shipments and review lower-cost transport options where practical.",["Shipment schedule","Mode alternatives","Carrier contracts"]),("Escalate verified cost impact","Escalate when actual cost variance exceeds internal thresholds.",["Budget variance","Fuel surcharge","Critical shipments"])],
"areas":["Finance","Procurement","Logistics","Operations"],"correlations":[(109,"Both reflect the same global crude-price and Middle East supply environment."),(101,"Both connect energy-market conditions to transport fuel exposure.")]},
109: {
"summary":"U.S. crude futures settled sharply lower as Middle East tensions eased and Saudi exports improved. For Test Electronics, this is a Low Financial signal because lower crude prices can reduce some fuel and freight cost pressure, although volatility remains. The move is a market signal, not a guaranteed company saving.",
"why":"Energy-price changes can affect diesel, carrier pricing and supplier operating costs. A lower benchmark can ease cost pressure if passed through to physical fuel and freight contracts, but timing and magnitude depend on contract structures and regional supply.",
"next":["Check whether lower crude prices are reaching diesel and carrier surcharges.","Review freight contracts with fuel-indexed pricing.","Compare current transport budgets with updated fuel assumptions."],
"impact":[("Diesel","Transportation, Logistics","Potential easing of fuel-cost pressure","Fuel surcharge formulas; carrier rates; transport budget"),("North America","Regional Logistics","Potential freight-cost improvement if lower fuel prices transmit","Regional freight quotes; shipment lanes")],
"objective":"Verify whether the crude-price move is translating into measurable transport-cost changes.",
"options":[("Monitor pass-through","Track diesel and carrier pricing rather than assuming crude moves pass through immediately.",["Diesel benchmarks","Carrier rates","Fuel surcharges"]),("Refresh cost assumptions","Update transport scenarios if the lower price persists.",["Budget assumptions","Freight quotes","Shipment plan"]),("Escalate opportunity","Escalate only if verified savings or capacity changes affect sourcing decisions.",["Contract terms","Verified savings","Carrier capacity"])],
"areas":["Finance","Logistics","Procurement"],"correlations":[(391,"Both concern global crude prices and Middle East supply conditions."),(101,"Both connect energy-market movements with transport-fuel exposure.")]},
101: {
"summary":"Record U.S. diesel prices and isolated shortages are raising concern about fuel availability as well as cost. For Test Electronics, this is a High Financial signal because Diesel is a configured dependency and transport continuity depends on physical fuel availability.",
"why":"A move from high prices to localized availability problems would affect carriers, delivery schedules and potentially airfreight or road capacity. The current evidence does not establish that Test Electronics has a shortage or a specific exposed lane.",
"next":["Check diesel availability and fuel-surcharge exposure on critical U.S. lanes.","Review carrier continuity plans and alternative transport modes.","Identify shipments where a local fuel shortage would create a material service impact."],
"impact":[("Diesel","Transportation, Distribution, Fleet Operations","Fuel availability and cost pressure; delivery continuity risk","Fuel availability; carrier contracts; critical lanes; alternative modes")],
"objective":"Distinguish a broad fuel-price signal from confirmed physical fuel exposure in the company's transport network.",
"options":[("Monitor local availability","Track fuel availability by critical transport region.",["Station availability","Carrier notices","Regional inventories"]),("Protect critical shipments","Review alternate carriers, routes and transport modes.",["Critical shipments","Alternative carriers","Mode capacity"]),("Escalate verified shortage","Escalate when a critical lane is physically constrained and alternatives are limited.",["Lane exposure","Inventory cover","Delivery commitments"])],
"areas":["Logistics","Procurement","Operations","Finance"],"correlations":[(391,"Both concern the global Middle East energy shock feeding into fuel markets."),(109,"Both are crude/fuel-market signals affecting transportation economics.")]},
})

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
    return int(risk_id) in CURATED_REVIEW_RISK_IDS

def presentation_location(risk):
    if risk.id in CURATED_INDIA_RISK_IDS:
        return 'India'
    if risk.id in CURATED_GLOBAL_RISK_IDS:
        return 'Global'
    if risk.id in CURATED_US_RISK_IDS:
        return 'United States'
    return risk.event.location if risk.event else None

def curated_review_risk_ids():
    return CURATED_REVIEW_RISK_IDS

def presentation_risks(db):
    """Return real stored Risk rows selected for the presentation workspace."""
    rows = db.query(Risk).filter(Risk.id.in_(CURATED_REVIEW_RISK_IDS)).all()
    by_id = {row.id: row for row in rows}
    return [by_id[rid] for rid in sorted(CURATED_REVIEW_RISK_IDS) if rid in by_id]

# Research-backed India/global scenarios. The underlying Risk/Event remains the
# source of identity; these entries provide presentation-specific interpretation.
SCENARIOS.update({
701: {
"summary":"Nexperia and Tata Electronics announced a strategic partnership covering semiconductor manufacturing, assembly and testing in India. For Test Electronics, this is a High Supplier signal directly relevant to Semiconductors. It represents potential ecosystem diversification and local capacity development, not a confirmed improvement in the company's own component supply.",
"why":"Nexperia supplies chips used in consumer electronics, and the partnership adds Indian manufacturing, packaging and testing capacity. For Test Electronics, the useful question is whether existing or future semiconductor sourcing can use this ecosystem and whether qualification paths become more diverse. The current evidence does not identify the company's Nexperia exposure or approved suppliers.",
"next":["Map semiconductor BOM items and identify any Nexperia or equivalent power-control components.","Review supplier concentration and qualification requirements for components that could use Indian assembly/test capacity.","Track Dholera and Jagiroad production/qualification milestones before treating the new capacity as available supply."],
"impact":[("Semiconductors","Procurement, Supplier Qualification, Manufacturing","Potential sourcing diversification; future qualification capacity; reduced single-region concentration if qualified","Approved suppliers; component BOMs; qualification timelines; production milestones")],
"objective":"Determine whether India's expanding semiconductor ecosystem can create a qualified alternative or resilience path for critical components.",
"options":[("Monitor capacity build-out","Track manufacturing, packaging and testing milestones before changing sourcing.",["Production milestones","Qualification status","Supplier capacity"]),("Evaluate alternative sourcing","Identify components that could qualify through Indian semiconductor manufacturing or test partners.",["BOM exposure","Alternate suppliers","Technical qualification"]),("Escalate qualification opportunity","Escalate where a critical component has high concentration and a credible alternative becomes available.",["Single-source exposure","Qualification lead time","Supply commitment"])],
"areas":["Procurement","Engineering","Supplier Management","Operations"],
"correlations":[(224,"Both concern India's battery/semiconductor supply-chain ecosystem and local sourcing development."),(1131,"Both concern India's longer-term shift in technology and energy infrastructure relevant to electronics.")],
},
224: {
"summary":"E3 Lithium signed a non-binding memorandum to potentially supply battery-grade lithium carbonate to India's Epsilon CAM. For Test Electronics, this is a Medium Supplier signal directly relevant to Lithium and Batteries. The MoU is a potential future supply arrangement, not a committed source for Test Electronics.",
"why":"A new lithium-carbonate supply pathway into India could diversify battery-material sourcing and reduce concentration in established supply routes if it reaches production and qualification. Test Electronics' battery suppliers, material specifications and purchase volumes are not stored.",
"next":["Review battery material supplier concentration and geographic exposure.","Track the Clearwater project's production and qualification milestones.","Identify whether future battery suppliers could qualify material from this route."],
"impact":[("Lithium","Battery Procurement, Supplier Management, Manufacturing","Potential material-source diversification; future lithium availability; qualification opportunity","Material specifications; approved suppliers; production capacity; qualification schedule"),("Batteries","Product Engineering, Manufacturing, Procurement","Potential diversification of battery-material inputs","Battery BOMs; cell suppliers; chemistry requirements")],
"objective":"Assess whether the emerging Canada-to-India lithium supply route could become a credible qualified source for battery materials.",
"options":[("Monitor project progress","Track commercial production, quality specifications and delivery readiness.",["Production timeline","Material quality","Delivery capability"]),("Evaluate diversification","Assess whether the route could reduce current lithium supplier concentration.",["Supplier concentration","Current contracts","Alternative capacity"]),("Escalate qualification","Begin supplier qualification only when commercial material and technical documentation are available.",["Samples","Certification","Commercial terms"])],
"areas":["Procurement","Supplier Management","Engineering","Operations"],
"correlations":[(701,"Both concern development of alternative supply capacity for India's electronics and battery ecosystem."),(95,"Both concern Indian industrial inputs and energy/material availability.")],
},
715: {
"summary":"India's growth outlook was raised while El Nino-related food and inflation risks remained a concern. For Test Electronics, this is a Medium Financial signal because demand conditions and input-cost pressure can influence electronics planning. It does not establish a company-specific demand change.",
"why":"Changes in Indian growth and food/energy conditions can affect consumer demand, operating costs and working-capital planning. The company-specific sales exposure, inventory levels and supplier costs are not stored.",
"next":["Review India demand assumptions for consumer-electronics products.","Check whether energy, logistics or imported-input costs have moved against the operating plan.","Monitor agricultural and energy conditions that could affect consumer spending or input inflation."],
"impact":[("Electricity","Operations, Cost Planning","Potential operating-cost pressure from energy conditions","Energy budget; facility consumption; tariff exposure"),("North America","Regional Planning, Sourcing","Potential changes in trade and demand assumptions","Sales exposure; sourcing lanes; landed costs")],
"objective":"Check whether the revised India macro outlook changes demand or cost assumptions used in supply-chain planning.",
"options":[("Monitor demand indicators","Track consumer demand and input-cost data alongside the growth forecast.",["Orders","Demand forecasts","Input costs"]),("Refresh planning assumptions","Update scenario assumptions if demand or costs materially diverge.",["Budget variance","Inventory plan","Demand forecast"]),("Escalate material deviation","Escalate only where verified demand/cost changes affect supply commitments.",["Customer orders","Inventory exposure","Supplier commitments"])],
"areas":["Finance","Sales Planning","Operations","Procurement"],
"correlations":[(95,"Both reflect Indian industrial and energy conditions affecting planning assumptions."),(1131,"Both concern structural changes in India's economy and energy use.")],
},
95: {
"summary":"India's August core-sector growth slowed to 4.8% as coal, crude oil, natural gas and fertilizer output weakened while electricity and cement remained stronger. For Test Electronics, this is a Medium Financial signal relevant to Electricity and Coal because industrial input conditions can affect operating costs and supplier activity.",
"why":"The mixed sector data matters because energy and industrial inputs sit upstream of manufacturing and logistics. A slowdown in coal or gas output can tighten energy conditions even when electricity generation remains strong. Test Electronics' facility energy contracts and supplier exposure are not stored.",
"next":["Review electricity and energy procurement assumptions for Indian operations.","Identify suppliers dependent on coal, gas or fertilizer-intensive industrial inputs.","Track whether the weakness persists for more than one reporting period."],
"impact":[("Electricity","Facilities, Manufacturing, Operations","Potential energy-cost or availability pressure if weakness persists","Power contracts; consumption; tariff changes"),("Coal","Industrial Supplier Network, Energy","Potential upstream input pressure for energy-intensive suppliers","Supplier energy exposure; production capacity; lead times")],
"objective":"Determine whether Indian core-sector weakness is translating into a measurable supply or operating-cost exposure.",
"options":[("Monitor sector data","Track the next core-sector releases and energy indicators.",["Coal output","Gas output","Electricity generation"]),("Review supplier exposure","Identify suppliers whose production depends on affected industrial inputs.",["Supplier map","Production capacity","Lead times"]),("Escalate persistent pressure","Escalate only if supplier or facility data confirms material exposure.",["Supplier disruption","Cost variance","Inventory cover"])],
"areas":["Operations","Procurement","Finance","Supplier Management"],
"correlations":[(1131,"Both concern India's evolving electricity and energy system."),(701,"Both affect the wider Indian manufacturing ecosystem relevant to electronics supply.")],
},
1131: {
"summary":"An IEA outlook indicates India's electrification rate could rise substantially by 2035, with transport electrification a major contributor. For Test Electronics, this is a Low Financial signal relevant to Electricity and Batteries because it points to a long-term shift in energy and transport demand rather than an immediate disruption.",
"why":"Greater electrification can change demand for batteries, power electronics, charging infrastructure and electricity capacity. It may also reduce some fuel dependence over time. The company's product roadmap and exposure to these markets are not stored.",
"next":["Identify products or components exposed to electrification and power-electronics demand.","Review battery and power-electronics supplier capacity for long-term planning.","Assess whether transport electrification changes the company's logistics or energy assumptions."],
"impact":[("Electricity","Product Planning, Facilities, Energy Procurement","Long-term power demand and infrastructure considerations","Power requirements; energy plans; grid exposure"),("Batteries","Product Engineering, Procurement","Potential growth in battery-related demand and sourcing requirements","Battery roadmap; cell supply; qualification capacity")],
"objective":"Translate the long-term electrification trend into concrete product, battery and energy planning questions.",
"options":[("Monitor market transition","Track electrification adoption and supplier capacity.",["Market adoption","Supplier capacity","Technology roadmap"]),("Evaluate strategic exposure","Map products and components that could benefit from or be constrained by the transition.",["Product portfolio","Battery BOMs","Power-electronics exposure"]),("Escalate planning change","Escalate when verified demand or supplier constraints warrant a roadmap adjustment.",["Demand forecast","Capacity commitments","Supplier qualification"])],
"areas":["Product Engineering","Procurement","Operations","Strategy"],
"correlations":[(224,"Both concern battery-material and energy-transition supply development."),(701,"Both concern structural changes in India's electronics supply ecosystem.")],
},
391: {
"summary":"Crude prices rose as U.S.-Iran negotiations remained unresolved and oil flows through the Strait of Hormuz faced continued uncertainty. For Test Electronics, this is a High Financial signal because global energy prices can transmit into transport, manufacturing and logistics costs. It does not establish a direct company loss.",
"why":"Crude-price volatility can feed diesel, marine fuel, freight rates and energy costs across global supply chains. The company-specific sensitivity depends on carrier contracts, energy procurement and shipment volume, none of which are stored.",
"next":["Review fuel and freight assumptions in current budgets.","Check carrier fuel-surcharge exposure and major ocean/road lanes.","Identify energy-intensive suppliers and time-critical shipments vulnerable to freight-cost changes."],
"impact":[("Diesel","Transportation, Logistics","Fuel and freight-cost volatility","Carrier surcharges; transport budget; shipment lanes"),("Ports","International Logistics, Import/Export","Freight and route-cost pressure","Port routes; freight quotes; transit times"),("Electricity","Operations, Facilities","Indirect energy-cost pressure","Energy contracts; consumption; tariff exposure")],
"objective":"Determine how much of the company's logistics and operating cost base is sensitive to global energy-price volatility.",
"options":[("Monitor energy markets","Track crude, diesel and freight indicators together.",["Crude benchmarks","Diesel prices","Freight rates"]),("Reduce exposure","Consolidate shipments and review lower-cost transport options where practical.",["Shipment schedule","Mode alternatives","Carrier contracts"]),("Escalate verified cost impact","Escalate when actual cost variance exceeds internal thresholds.",["Budget variance","Fuel surcharge","Critical shipments"])],
"areas":["Finance","Procurement","Logistics","Operations"],
"correlations":[(109,"Both reflect the same global crude-price and Middle East supply environment."),(101,"Both connect energy-market conditions to transport fuel exposure.")],
},
109: {
"summary":"U.S. crude futures settled sharply lower as Middle East tensions eased and Saudi exports improved. For Test Electronics, this is a Low Financial signal because lower crude prices can reduce some fuel and freight cost pressure, although volatility remains. The move is a market signal, not a guaranteed company saving.",
"why":"Energy-price changes can affect diesel, carrier pricing and supplier operating costs. A lower benchmark can ease cost pressure if passed through to physical fuel and freight contracts, but the timing and magnitude depend on contract structures and regional supply.",
"next":["Check whether lower crude prices are reaching diesel and carrier surcharges.","Review freight contracts with fuel-indexed pricing.","Compare current transport budgets with updated fuel assumptions."],
"impact":[("Diesel","Transportation, Logistics","Potential easing of fuel-cost pressure","Fuel surcharge formulas; carrier rates; transport budget"),("North America","Regional Logistics","Potential freight-cost improvement if lower fuel prices transmit","Regional freight quotes; shipment lanes")],
"objective":"Verify whether the crude-price move is translating into measurable transport-cost changes.",
"options":[("Monitor pass-through","Track diesel and carrier pricing rather than assuming crude moves pass through immediately.",["Diesel benchmarks","Carrier rates","Fuel surcharges"]),("Refresh cost assumptions","Update transport scenarios if the lower price persists.",["Budget assumptions","Freight quotes","Shipment plan"]),("Escalate opportunity","Escalate only if verified savings or capacity changes affect sourcing decisions.",["Contract terms","Verified savings","Carrier capacity"])],
"areas":["Finance","Logistics","Procurement"],
"correlations":[(391,"Both concern global crude prices and Middle East supply conditions."),(101,"Both connect energy-market movements with transport-fuel exposure.")],
},
101: {
"summary":"Record U.S. diesel prices and isolated shortages are raising concern about fuel availability as well as cost. For Test Electronics, this is a High Financial signal because Diesel is a configured dependency and transport continuity depends on physical fuel availability.",
"why":"A move from high prices to localized availability problems would affect carriers, delivery schedules and potentially airfreight or road capacity. The current evidence does not establish that Test Electronics has a shortage or a specific exposed lane.",
"next":["Check diesel availability and fuel-surcharge exposure on critical U.S. lanes.","Review carrier continuity plans and alternative transport modes.","Identify shipments where a local fuel shortage would create a material service impact."],
"impact":[("Diesel","Transportation, Distribution, Fleet Operations","Fuel availability and cost pressure; delivery continuity risk","Fuel availability; carrier contracts; critical lanes; alternative modes")],
"objective":"Distinguish a broad fuel-price signal from confirmed physical fuel exposure in the company's transport network.",
"options":[("Monitor local availability","Track fuel availability by critical transport region.",["Station availability","Carrier notices","Regional inventories"]),("Protect critical shipments","Review alternate carriers, routes and transport modes.",["Critical shipments","Alternative carriers","Mode capacity"]),("Escalate verified shortage","Escalate when a critical lane is physically constrained and alternatives are limited.",["Lane exposure","Inventory cover","Delivery commitments"])],
"areas":["Logistics","Procurement","Operations","Finance"],
"correlations":[(391,"Both concern the global Middle East energy shock feeding into fuel markets."),(109,"Both are crude/fuel-market signals affecting transportation economics.")],
},
})



# ---------------------------------------------------------------------------
# Dynamic presentation curation
# ---------------------------------------------------------------------------
# The presentation workspace is selected from the real stored event/risk
# stream. This keeps the review set useful without inventing database rows.
# The existing SCENARIOS above remain valid for older explicitly curated rows;
# these functions provide a consistent fallback for additional high-quality
# supply-chain signals.

DYNAMIC_REVIEW_RISK_IDS = set()
_REVIEW_COUNTS = {"United States": 13, "India": 15, "Global": 22}

_REVIEW_DEPENDENCIES = {
    "Semiconductors": ("semiconductor", "semiconductors", "chip", "chips", "wafer", "foundry", "memory"),
    "Batteries": ("battery", "batteries", "cell", "cells", "cathode", "anode"),
    "Lithium": ("lithium",),
    "Diesel": ("diesel", "fuel", "refinery", "refined products"),
    "Electricity": ("electricity", "power grid", "grid", "power generation", "utility"),
    "Coal": ("coal",),
    "Ports": ("port", "ports", "shipping", "vessel", "container", "freight", "maritime"),
    "Road": ("road", "truck", "trucking", "highway"),
    "Rail": ("rail", "railway"),
    "Cloud Services": ("cloud", "data center", "data centre"),
    "Telecom": ("telecom", "network outage", "communications"),
    "North America": ("united states", "u.s.", "north america", "canada"),
}

_REVIEW_SUPPLY_TERMS = (
    "supply chain", "supplier", "sourcing", "shortage", "bottleneck", "capacity",
    "production", "manufacturing", "factory", "plant", "shipment", "shipping",
    "freight", "port", "rail", "truck", "logistics", "export", "import", "tariff",
    "sanction", "trade", "refinery", "fuel", "diesel", "oil", "crude", "gas",
    "electricity", "power", "coal", "semiconductor", "chip", "battery", "lithium",
    "nickel", "cobalt", "rare earth", "mineral", "weather", "flood", "storm",
    "hurricane", "earthquake", "drought", "cyberattack", "cyber", "outage",
    "congestion", "rerouting", "blockade", "embargo", "energy",
)

_REVIEW_NOISE_TERMS = (
    "cricket", "football", "soccer", "cycling", "marathon", "olympic", "asian games",
    "festival", "concert", "celebrity", "movie", "music", "garbage truck", "air defense",
    "missile interception", "sports", "tournament", "match", "fashion", "entertainment",
    "lottery", "horoscope",
)

def _review_text(risk):
    event = risk.event
    return " ".join(str(getattr(event, field, "") or "") for field in ("title", "description", "category")).casefold()

def _review_location(risk):
    value = str(risk.event.location if risk.event else "").strip()
    lower = value.casefold()
    if lower in {"india", "india, india"} or lower.endswith(", india"):
        return "India"
    if lower in {"united states", "usa", "us"} or lower.endswith(", united states") or lower.endswith(", usa"):
        return "United States"
    return "Global"

def _review_dependency_matches(risk):
    text = _review_text(risk)
    matches = []
    for dependency, terms in _REVIEW_DEPENDENCIES.items():
        if any(term in text for term in terms):
            matches.append(dependency)
    return matches

def _review_candidate_score(risk):
    text = _review_text(risk)
    if not risk.event or not risk.event.title:
        return -10_000
    if any(term in text for term in _REVIEW_NOISE_TERMS):
        return -10_000

    score = 0
    dependencies = _review_dependency_matches(risk)
    score += min(len(dependencies), 4) * 22
    score += min(sum(text.count(term) for term in _REVIEW_SUPPLY_TERMS), 8) * 4

    severity = str(risk.severity or "").casefold()
    score += {"critical": 24, "high": 18, "medium": 10, "low": 4}.get(severity, 0)

    category = str(risk.event.category or "").casefold()
    if any(term in category for term in ("supply", "logistics", "energy", "weather", "technology", "trade")):
        score += 8

    created = risk.event.published_at or risk.event.event_time or risk.event.created_at
    if created:
        age_days = max(0, (datetime.now(timezone.utc) - (
            created.replace(tzinfo=timezone.utc) if created.tzinfo is None else created
        )).total_seconds() / 86400)
        if age_days <= 7:
            score += 12
        elif age_days <= 14:
            score += 6
        elif age_days > 45:
            score -= 12

    return score

def _dedupe_review_candidates(rows):
    seen = set()
    result = []
    for risk in rows:
        title = " ".join((risk.event.title or "").casefold().split())
        if title in seen:
            continue
        seen.add(title)
        result.append(risk)
    return result

def presentation_risks(db):
    """Return a balanced presentation set from real stored Risk/Event rows."""
    global DYNAMIC_REVIEW_RISK_IDS, CURATED_REVIEW_RISK_IDS
    all_rows = (
        db.query(Risk)
        .join(Risk.event)
        .filter(Risk.status != "Resolved")
        .order_by(Risk.created_at.desc())
        .limit(800)
        .all()
    )

    buckets = {"United States": [], "India": [], "Global": []}
    for risk in _dedupe_review_candidates(all_rows):
        location = _review_location(risk)
        score = _review_candidate_score(risk)
        if score < 18:
            continue
        buckets[location].append((score, risk))

    selected = []
    for location, target in _REVIEW_COUNTS.items():
        ranked = sorted(
            buckets[location],
            key=lambda item: (item[0], float(item[1].risk_score or 0)),
            reverse=True,
        )
        selected.extend(risk for _, risk in ranked[:target])

    # If a bucket is short because its current stream is sparse, fill it with
    # the strongest remaining supply-chain signals rather than displaying weak
    # unrelated content.
    selected_ids = {risk.id for risk in selected}
    if len(selected) < sum(_REVIEW_COUNTS.values()):
        remaining = sorted(
            [
                (score, risk)
                for bucket in buckets.values()
                for score, risk in bucket
                if risk.id not in selected_ids
            ],
            key=lambda item: (item[0], float(item[1].risk_score or 0)),
            reverse=True,
        )
        for _, risk in remaining:
            if len(selected) >= sum(_REVIEW_COUNTS.values()):
                break
            selected.append(risk)
            selected_ids.add(risk.id)

    DYNAMIC_REVIEW_RISK_IDS = selected_ids
    CURATED_REVIEW_RISK_IDS = set(selected_ids)
    CURATED_US_RISK_IDS = {r.id for r in selected if _review_location(r) == "United States"}
    CURATED_INDIA_RISK_IDS = {r.id for r in selected if _review_location(r) == "India"}
    CURATED_GLOBAL_RISK_IDS = {r.id for r in selected if _review_location(r) == "Global"}
    return selected

def presentation_location(risk):
    if risk.id in DYNAMIC_REVIEW_RISK_IDS:
        return _review_location(risk)
    return risk.event.location if risk.event else None

def is_review_risk(risk_id: int) -> bool:
    return int(risk_id) in DYNAMIC_REVIEW_RISK_IDS

def curated_review_risk_ids():
    return DYNAMIC_REVIEW_RISK_IDS

def _generic_review_subject(risk, event):
    deps = _review_dependency_matches(risk)
    if deps:
        return ", ".join(deps[:3])
    if event.category:
        return str(event.category)
    return str(risk.risk_type or risk.risk_name or "the monitored supply-chain signal")

def _generic_review_sections(risk, event, company_name, industry):
    subject = _generic_review_subject(risk, event)
    deps = _review_dependency_matches(risk)
    dep_text = ", ".join(deps) if deps else subject
    title = event.title or "Stored event signal"
    summary = (
        f"{title} is a {risk.severity or 'unrated'} {risk.risk_type or risk.risk_name or 'supply-chain'} "
        f"signal in {presentation_location(risk) or event.location or 'the monitored network'}. "
        f"The strongest configured company-relevant areas are {dep_text}. "
        f"The stored event does not by itself establish a loss or disruption at {company_name}."
    )
    why = (
        f"For {company_name}, the relevant review question is whether the external signal changes "
        f"availability, cost, lead time, routing, supplier capacity or demand for {dep_text}. "
        f"SupplySentry does not store supplier contracts, purchase volumes, inventory cover, shipment "
        f"volumes or customer commitments, so exposure must be verified internally."
    )
    next_steps = [
        f"Map current {dep_text} suppliers, routes or operating dependencies against the event.",
        f"Check open orders, inventory cover and committed production or delivery dates exposed to {dep_text}.",
        "Track the source event for persistence, escalation or reversal before changing supply-chain plans.",
    ]
    sections = {
        "investigation_summary": [_statement(summary, "E1", title, "fact")],
        "why_this_matters": [
            _statement(why, "E1", title),
            _statement(
                f"{company_name}'s quantitative exposure remains unknown because internal contracts, volumes and inventory data are not stored.",
                "E3",
                f"{company_name} / {industry}",
            ),
        ],
        "supporting_evidence": [
            _statement(
                f"Stored assessment: {risk.severity or 'Unrated'} severity, {risk.risk_type or risk.risk_name or 'Unspecified'} risk type, risk score {float(risk.risk_score or 0):.2f}.",
                "E2",
                f"{risk.severity} / {risk.risk_type or risk.risk_name}",
            ),
            _statement(
                f"Stored event location: {event.location or 'not specified'}; source: {event.source or 'not specified'}.",
                "E1",
                title,
            ),
        ],
        "related_intelligence": [],
        "what_to_investigate_next": [_statement(item, "E1", title) for item in next_steps],
    }
    return sections, deps, subject

def build_review_investigation(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    if not is_review_risk(risk.id):
        return None
    sections, deps, subject = _generic_review_sections(risk, event, company_name, industry)
    return {
        "investigation_id": f"review-{risk.id}",
        "target": {"risk_id": risk.id, "event_id": event.id},
        "generated_at": datetime.now(timezone.utc),
        "model": {"provider": "curated-review", "name": "SupplySentry Review Content", "quantization": None},
        "sections": sections,
        "evidence": [
            {"ref": "E1", "evidence_type": "event", "label": "Stored event", "data": {"id": event.id, "title": event.title, "location": event.location, "category": event.category, "source": event.source}},
            {"ref": "E2", "evidence_type": "risk", "label": "Stored risk assessment", "data": {"id": risk.id, "severity": risk.severity, "risk_type": risk.risk_type, "risk_score": risk.risk_score}},
            {"ref": "E3", "evidence_type": "company_context", "label": "Company profile", "data": {"company_name": company_name, "industry": industry, "dependencies": deps}},
        ],
        "warnings": ["Curated review content is grounded in the stored event and risk record and is decision support only."],
        "decision_support_only": True,
    }

def build_review_impact(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    if not is_review_risk(risk.id):
        return None
    deps = _review_dependency_matches(risk) or [risk.risk_type or risk.risk_name or "Supply-chain activity"]
    mappings = []
    for dependency in deps[:4]:
        area = {
            "Semiconductors": "Procurement, Supplier Qualification, Electronics Production",
            "Batteries": "Procurement, Product Engineering, Manufacturing",
            "Lithium": "Materials Procurement, Supplier Management, Manufacturing",
            "Diesel": "Transportation, Logistics, Distribution",
            "Electricity": "Facilities, Manufacturing, Operations",
            "Coal": "Energy-Intensive Supplier Network, Operations",
            "Ports": "International Logistics, Import/Export, Transportation",
            "Road": "Distribution, Transportation, Last Mile",
            "Rail": "Inbound Logistics, Transportation",
            "Cloud Services": "Technology Operations, Digital Supply Chain",
            "Telecom": "Technology Operations, Communications",
            "North America": "Regional Sourcing, Logistics Planning",
        }.get(dependency, "Procurement, Operations, Risk Management")
        impacts = (
            f"Potential change in {dependency.lower()} availability, cost, lead time or continuity "
            "depending on the company's actual exposure."
        )
        checks = (
            f"Current {dependency} supplier or route exposure; open commitments; inventory or capacity "
            "cover; qualified alternatives."
        )
        mappings.append({
            "dependency": dependency,
            "category": "company_dependency",
            "relevance": "direct" if dependency in deps else "indirect",
            "matched_terms": [dependency],
            "matched_on": "stored event content and configured company dependency",
            "supply_chain_areas": [x.strip() for x in area.split(",")],
            "potential_impacts": [impacts],
            "verification_checks": [checks],
        })
    return {
        "risk_id": risk.id,
        "event_id": event.id,
        "company_available": True,
        "company_name": company_name,
        "industry": industry,
        "risk": {"id": risk.id, "severity": risk.severity, "risk_type": risk.risk_type or risk.risk_name, "risk_score": risk.risk_score, "status": risk.status, "created_at": risk.created_at.isoformat() if risk.created_at else None, "prediction": None},
        "event": {"id": event.id, "title": event.title, "description": event.description, "category": event.category, "event_type": event.event_type, "location": event.location, "source": event.source},
        "relevance": "direct" if _review_dependency_matches(risk) else "indirect",
        "relevance_reason": f"Review mapping based on configured Test Electronics dependencies.",
        "summary": f"Potential exposure areas are mapped from the stored event and configured company dependencies. This does not claim that {company_name} has experienced these impacts.",
        "mappings": mappings,
        "data_limitations": DATA_LIMITATIONS,
    }

def build_review_response_plan(risk, event, company_name="Test Electronics", industry="Consumer Electronics"):
    if not is_review_risk(risk.id):
        return None
    deps = _review_dependency_matches(risk)
    subject = _generic_review_subject(risk, event)
    scenario = "materials_and_supply" if any(x in {"Semiconductors", "Batteries", "Lithium"} for x in deps) else (
        "fuel_and_energy" if any(x in {"Diesel", "Electricity", "Coal"} for x in deps) else (
            "logistics_and_transport" if any(x in {"Ports", "Road", "Rail"} for x in deps) else "general"
        )
    )
    options = [
        ("Option 1: Monitor and Verify", f"Verify the current {subject} exposure before changing plans.", ["Current internal exposure", "Current source status", "Supplier/route commitments"]),
        ("Option 2: Reduce Near-Term Exposure", f"Review feasible sourcing, routing, timing or inventory actions affecting {subject}.", ["Alternative suppliers or routes", "Inventory cover", "Critical delivery commitments"]),
        ("Option 3: Escalate for Review", f"Escalate if verified {subject} exposure is business-critical and alternatives are limited.", ["Exposure magnitude", "Business criticality", "Alternative capacity"]),
    ]
    return {
        "risk_id": risk.id, "event_id": event.id, "scenario": scenario,
        "generated_by": "curated-review", "is_demo_template": False,
        "company_context_available": True, "company_name": company_name, "company_industry": industry,
        "company_relevance": "direct" if deps else "indirect",
        "matched_dependencies": deps,
        "risk_summary": f"{event.title or 'Stored event'} is being reviewed for its potential effect on {subject}.",
        "response_objective": f"Determine whether the event creates a verified supply-chain exposure for {company_name} and identify proportionate response options.",
        "immediate_checks": [
            f"Verify current {subject} exposure against internal suppliers, routes, contracts and inventory.",
            "Check whether the event is persistent, worsening or already reversing.",
            "Confirm whether a qualified alternative exists before changing commitments.",
        ],
        "response_options": [{"name": name, "what_to_check": checks, "why": why, "information_required": checks} for name, why, checks in options],
        "information_required": [item for _, _, checks in options for item in checks][:8],
        "escalation_conditions": [
            "Internal data confirms material exposure to the event.",
            "The affected activity is business-critical and practical alternatives are limited.",
            "The signal persists or worsens across subsequent monitoring cycles.",
        ],
        "responsible_areas": ["Procurement", "Operations", "Logistics", "Finance"],
        "platform_recommendation": None,
        "notes": ["Prepared from the stored event, risk assessment and company profile.", "Options are for human review; no automated business action is taken."],
        "decision_support_only": True,
    }

def build_review_correlations(db, risk_id):
    if risk_id not in DYNAMIC_REVIEW_RISK_IDS:
        return None
    target = db.query(Risk).filter(Risk.id == risk_id).first()
    if target is None or target.event is None:
        return None
    candidates = [risk for risk in presentation_risks(db) if risk.id != risk_id and risk.event is not None]
    target_deps = set(_review_dependency_matches(target))
    target_tokens = set((target.event.title or "").casefold().split())
    rows = []
    for candidate in candidates:
        deps = set(_review_dependency_matches(candidate))
        shared = target_deps & deps
        same_type = str(target.risk_type or "").casefold() == str(candidate.risk_type or "").casefold()
        same_category = str(target.event.category or "").casefold() == str(candidate.event.category or "").casefold()
        score = len(shared) * 30 + (20 if same_type and target.risk_type else 0) + (15 if same_category else 0)
        candidate_tokens = set((candidate.event.title or "").casefold().split())
        overlap = len(target_tokens & candidate_tokens)
        if overlap:
            score += min(20, overlap * 5)
        if score < 35:
            continue
        score = min(95, score)
        reasons = []
        if shared:
            reasons.append(f"Shared configured dependency: {', '.join(sorted(shared))}.")
        if same_type and target.risk_type:
            reasons.append(f"Both are classified as {target.risk_type}.")
        if same_category:
            reasons.append(f"Both are in the {target.event.category} event category.")
        if overlap:
            reasons.append("Their event titles share substantive supply-chain terms.")
        rows.append((score, candidate, reasons))
    rows.sort(key=lambda item: (item[0], float(item[1].risk_score or 0)), reverse=True)
    result = []
    for score, related, reasons in rows[:5]:
        result.append({
            "risk_id": related.id,
            "event_id": related.event.id,
            "event_title": related.event.title or related.risk_name,
            "severity": related.severity,
            "risk_type": related.risk_type or related.risk_name,
            "location": related.event.location,
            "event_category": related.event.category,
            "correlation_score": score,
            "relationship_level": "high" if score >= 75 else "moderate",
            "relationship_label": "Strong relationship" if score >= 75 else "Meaningful similarity",
            "reasons": reasons,
            "shared_company_dependencies": sorted(target_deps & set(_review_dependency_matches(related))),
            "days_apart": None,
        })
    return {
        "risk_id": risk_id,
        "event_id": target.event.id,
        "correlations": result,
        "total_candidates_considered": len(candidates),
        "analysis_window_days": 7,
        "message": None if result else "No strongly related review signals identified.",
        "disclaimer": "Correlation scores describe similarity between selected SupplySentry signals; they do not establish causation.",
        "company_context_available": True,
    }
