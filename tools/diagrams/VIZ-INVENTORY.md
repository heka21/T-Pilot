# Visualisation push: inventory and to-do list

The user (a visual learner) asked on 2026-10-10 for more of every kind of visual (interactive widgets, timeline
animations, 3D explorers, static diagrams) for every concept in every RPLA and PPLA lesson, then the same in the
narrated Watch mode. This file is the to-do list and the review checklist. Brief for builders:
`tools/diagrams/AUTHORING.md` (read the "Interactive widgets and timelines" section).

Baseline before the push: 301 diagrams (36 animated), 16 widgets (4 Three.js explorers), 49 widget embeds;
`python -m app.seed.lint_lessons --interactive` flagged 40 lessons with nothing to move or watch.

Status marks: `[ ]` to do, `[x]` built and embedded, `(ex)` exemplar built by the lead.

## Shared catalogue (one widget, several lessons)

Built in Phase 1a by themed agents; each owns its slugs. "Lessons" are where Phase 1b embeds them (the builder
embeds in the first lesson listed; unit agents embed the rest). Existing static diagrams on the same topic stay;
the widget goes beside them with a different question.

### Weather (agent: weather)
- (ex) `sea-breeze-day` timeline: Fremantle Doctor through a summer day, gradient easterly slider. RMTC 2.1 [x], PMTC 2.5, PMTC 2.3, RMTC 2.3
- (ex) `taf-arrival-check` widget: TAF groups vs ETA, PPL window and holding fuel. RMTC 2.2 [x], PFRA 2.4 [x], POPC 2.4 [x], POPC 2.5, POPC 2.6
- [x] `overnight-cooling` timeline: temperature profile through a clear night, inversion, T meets Td → radiation fog, dawn low-level jet, burn-off. RMTC 2.1, RMTC 2.3, PMTC 2.2, PMTC 2.4, PMTC 2.5
- [x] `thunderstorm-stages` timeline: cumulus → mature (downdraught, gust front, microburst) → dissipating, with the three ingredients as toggles. RMTC 2.1, RMTC 2.3, PMTC 2.3, PMTC 2.6, PMTC 2.7
- [x] `scarp-wave-and-rotor` widget: wind speed and stability sliders over the Darling Scarp → no wave / rotor / lee wave with lenticulars. RMTC 2.1, RMTC 2.3, PMTC 2.7
- [x] `pressure-systems-wind` widget: drag isobar spacing and pick high/low → Southern Hemisphere circulation, Buys Ballot, wind strength, friction backing near the surface. RMTC 2.1, PMTC 2.5
- [x] `okta-sky` widget: add cloud to a sky dome → oktas, FEW/SCT/BKN/OVC, ceiling or not. RMTC 2.2, PMTC 2.3, PFRA 2.4
- [x] `cloud-base-from-spread` widget: temperature and dew point → cumulus base (400 ft per °C as the lessons give it), parcel rising. PMTC 2.3, PMTC 2.2, RMTC 2.1
- [x] `wind-gradient-approach` timeline: descending through a wind gradient or shear on final and on climb-out → IAS loss/gain, sink. RMTC 2.3, RBKA 3.7, RBKA 3.3, RBKA 3.6, PMTC 2.7, PAKA 3.1, POPA 2.2, BAKC 6.2

### Time, rules and documents (agent: rules)
- [x] `utc-local-clock` widget: drag WST ↔ UTC with the date rollover, PRD/NOTAM activity windows in UTC, summer-time zones (east coast) for contrast. BAKC 2.3, BAKC 5.2, RFRC 2.6, PFRA 2.1, PFRA 2.3, PNVC 2.2, POPC 2.3, POPC 2.5, PAKC 3.1
- [x] `sartime-phases` timeline: SARTIME passes → uncertainty / alert / distress phases and who does what. RFRC 2.7, PFRA 2.9, PAKC 3.7, PAKC 3.8, POPC 2.4
- [x] `recency-window` widget: drag "today" → which recency and currency requirements are met (figures from RFRC 2.2 / PFRA 2.2 only). RFRC 2.2, PFRA 2.2
- [x] `vmc-minima-picker` widget: airspace class and height → visibility and cloud clearance, with the aeroplane and cloud drawn to scale. RFRC 2.3, PFRA 2.6, PMTC 2.4, PMTC 2.7
- [x] `cruising-level-by-track` widget: rotate the magnetic track → odd/even thousands + 500, VFR levels. RFRC 2.3, PFRA 2.6, POPC 2.5
- [x] `maintenance-release-check` widget: enter date and hours → MR valid or not, endorsements. BAKC 6.1, RFRC 2.1, POPC 2.7

### Aerodynamics and limits (agent: aero)
- (ex) `drag-curve-explorer` widget: parasite/induced/total drag, best L/D, glide distance, weight, power required, endurance and range with wind. BAKC 4.2 [x], RBKA 3.1 [x], RBKA 3.4 [x], POPA 2.5 [x]
- [x] `lift-curve-flap` widget: CL vs angle of attack with flap toggle; lift formula sliders (ρ, V, CL, S); stall at the critical angle. BAKC 4.1, BAKC 4.2, RBKA 3.1, RBKA 3.2, RBKA 3.6, RBKA 4.2, PAKA 2.2
- [x] `climb-performance` widget: power available vs required → excess power, ROC curve, Vx and Vy; weight, altitude and flap sliders. BAKC 4.3, RBKA 3.3, POPA 2.5
- [x] `climb-gradient-wind` widget: ROC and groundspeed → ft/NM, %, degrees; head/tailwind and an obstacle to clear. BAKC 4.3, BAKC 6.2, RBKA 3.3, PAKA 3.1, POPA 2.1, POPA 2.2, PNVC 2.4
- [x] `v-n-envelope` widget: drag a point (speed, g) on the V-n diagram, weight slider moves VA, gust lines. BAKC 6.3, RBKA 3.8, POPC 2.2
- [x] `asi-arcs-explorer` widget: ASI needle through the white/green/yellow arcs, VS0, VS1, VFE, VNO, VNE; flap load ∝ V² above VFE. BAKC 3.5, BAKC 6.3, RBKA 3.2, RBKA 4.2, POPC 2.2
- [x] `energy-trade` timeline: zoom climb trading kinetic for potential energy, KE ∝ V². BAKC 2.5, BAKC 4.1, RBKA 3.4, RBKA 3.7, POPA 2.2
- [x] `ground-effect-height` widget: height in wingspans → induced drag reduction, float, early lift-off. BAKC 6.2, RBKA 3.1, RBKA 3.7, PAKA 3.1, POPA 2.2
- [x] `g-load-effects` widget: load factor slider → stall speed factor, blood column, greyout/tunnel vision/blackout/G-LOC. PHFC 2.9, RBKA 3.5

### Performance and engines (agent: perf)
- [x] `takeoff-factor-stack` widget: toggles for surface, wet grass, slope, pressure height and temperature, weight, wind → distance bar against the available runway (factors only from the lessons). BAKC 6.2, RBKA 4.1, PAKA 3.1, POPA 2.1, POPA 2.2, POPA 2.4, POPC 2.3
- [x] `declared-distances-runway` widget: TORA/TODA/ASDA/LDA and a displaced threshold on a runway, take-off or landing direction. POPA 2.1, POPC 2.3, PFRA 2.5
- [x] `weight-limits-governs` widget: MTOW, climb-limited, landing-limited (with fuel burn) → lowest governs. BAKC 6.2, PAKA 3.1, POPA 2.2, POPA 2.4, POPC 2.1
- [x] `power-vs-altitude` widget: normally aspirated vs turbocharged power against altitude, full throttle height, critical altitude. BAKC 3.1, BAKC 6.2, RBKA 3.3, PAKC 2.1, PAKC 2.2, PAKA 3.1, POPA 2.2, POPA 2.3, POPA 2.5
- [x] `mixture-leaning` widget: mixture control → RPM, EGT, power; peak, rich of peak, rough. BAKC 3.1, BAKC 3.3, RBKA 2.1, PAKC 2.1, POPA 2.5
- [x] `carb-ice-risk` widget: OAT and dew point → risk band (from the lessons' chart) and power setting. BAKC 3.4, RBKA 2.1, PMTC 2.7
- [x] `carb-ice-build` timeline: ice building in the venturi, RPM decaying, chasing it with throttle, carb heat: drop then rise. BAKC 3.4, RBKA 2.1
- [x] `detonation-chamber` timeline: normal flame front vs detonation, with causes (lean, hot, high power, low octane) as toggles. BAKC 3.3, RBKA 2.1, PAKC 2.1, PAKC 2.2

### Instruments and navigation (agent: nav)
- [x] `pitot-static-sim` widget: block the pitot, drain or static port, climb or descend → ASI, altimeter, VSI; alternate static. BAKC 3.5, BAKC 2.2, PAKC 2.3
- [x] `airspeed-chain` widget: IAS → CAS → TAS (pressure height, temperature) → GS (wind). BAKC 2.2, PAKC 2.3, PNVC 2.4
- [x] `heading-converter` widget: true/magnetic/compass with variation and deviation, aeroplane dragged across WA's isogonals. BAKC 2.1, BAKC 3.5, PAKC 2.3, PNVC 2.1, PNVC 2.3, PNVC 2.4
- [x] `clock-code-bearing` widget: rotate the aeroplane, traffic stays put → clock code, relative bearing, magnetic bearing. BAKC 2.1, PHFC 2.7, PNVC 2.1, PNVC 2.6
- [x] `height-datums` widget: aeroplane over terrain with aerodrome elevation and QNH → height, altitude, elevation; GAF AMSL vs TAF AGL cloud base. BAKC 2.4, BAKC 3.5, RMTC 2.2, PMTC 2.3, PFRA 2.6, POPA 2.2
- [x] `compass-turning-errors` timeline: Southern Hemisphere turning and acceleration errors. PAKC 2.3, BAKC 3.5
- [x] `vhf-range-height` widget: height slider → line-of-sight range (1.23√h as the lessons give it), two stations. PAKC 3.10, PNVC 2.6
- [x] `vor-cdi` widget: drag the aeroplane round a VOR, set the OBS → CDI deflection and TO/FROM; DME slant range vs ground distance. PNVC 2.6, PNVC 2.7, GNSSC 2.1

### Human factors (agent: human)
- [x] `altitude-oxygen` widget: altitude → pressure, O2 partial pressure (21% constant), saturation, hypoxia stage, time of useful consciousness (figures from PHFC 2.11/2.12 only). PHFC 2.12, PHFC 2.11, PHFC 2.3, PHFC 2.4, PHFC 2.10, PMTC 2.1
- [x] `oxygen-chain` widget: break the chain at lungs / blood / circulation / cells → hypoxia type and examples. PHFC 2.12, PHFC 2.1, PHFC 2.2, PHFC 2.9, PHFC 2.10, PHFC 2.11
- [x] `ear-equalisation` timeline: climb vs descent, eustachian tube venting easily one way, blocked the other. PHFC 2.5, PHFC 2.1, PHFC 2.4
- [x] `canal-lag-turn` timeline: semicircular canal fluid through roll-in, sustained turn, roll-out → sensation vs reality, graveyard spiral. PHFC 2.7, PHFC 2.5, PHFC 2.8
- [x] `noise-dose` widget: dB level, hours, protection → dose against the lessons' limit and exchange rate. PHFC 2.6, PHFC 2.5
- [x] `stress-performance` widget: arousal slider along the inverted-U, with examples. PHFC 2.13, PHFC 2.1, PHFC 2.3, PHFC 2.15
- [x] `alcohol-timeline` timeline: drinks and finish time → blood alcohol falling at the lessons' rate, the 8-hour rule and the limit, hangover tail. PHFC 2.2, PHFC 2.1, RFRC 2.3

### 3D explorers (Fable agent, app/static/explorers.js; widget files content/widgets/<slug>.html)
- [x] `airspace-3d` Perth airspace steps (CTA steps, Class D Jandakot with tower hours, restricted areas) with the aeroplane flying under the steps. BAKC 5.1, RFRC 2.6, RFRC 2.3, PFRA 2.6, PNVC 2.3, POPC 2.5
- [x] `overhead-join-3d` (extend `circuitPath`): overhead join and descent on the dead side. RFRC 2.5, PAKC 3.4, PAKC 3.8, PFRA 2.5
- [x] `spin-vs-spiral-3d` with the instruments (ASI, turn coordinator) for each. RBKA 3.6, BAKC 6.3, POPC 2.2, PHFC 2.9
- [x] `gyro-precession-3d` spinning rotor: rigidity, precession 90° on, DI drift. BAKC 3.5, PAKC 2.3
- [x] `wake-vortices-3d` sinking and drifting with crosswind behind a heavy, your path above/upwind. BAKC 4.4
- [x] `crosswind-landing-3d` crab vs wing-down, ground track on the centreline. RBKA 3.7
- [dropped] `mountain-wave-3d` (covered by `scarp-wave-and-rotor`) airflow over a ridge with rotor and lenticulars. PMTC 2.7
- [x] `gnss-trilateration-3d` add satellites one by one, spheres meeting; RAIM fifth satellite. GNSSC 2.1
- [x] `cloud-genera-3d` the ten genera by height in a sky you orbit. PMTC 2.3
- [x] `minimum-heights-3d` built-up area vs elsewhere, 1,000 ft / 600 m and 500 ft / 300 m figures from RFRC 2.3. RFRC 2.3

## Per lesson (Phase 1b)

Each line: the lesson, its visuals before the push (d = diagrams, w = widget embeds), and the dynamic or spatial
concepts that still need a widget, timeline or explorer. Shared slugs above are the first choice; the rest are
lesson-specific widgets or animated diagrams for the unit agent to build. Text-heavy lessons also get 2 to 4
static diagrams. Existing widgets that fit are noted with "+existing".

### BAKC
- 2.1 Direction of flight (6d 0w): clock-code traffic as you rotate; T→M→C across the isogonals; heading vs track with a drift wind; runway heading → runway number. Shared: heading-converter, clock-code-bearing. +existing wind-triangle
- 2.2 Distance, speed and velocity (6d 1w): IAS→CAS→TAS→GS; groundspeed with head/tailwind; nautical mile = 1' of latitude on a globe; pitot vs static pressure with speed. Shared: airspeed-chain, pitot-static-sim
- 2.3 Time (4d 0w): dual UTC/WST clock with the date rollover; Australian time zones with a summer-time toggle; adding times with the carry at 60. Shared: utc-local-clock
- 2.4 Units of measurement (3d 2w): height/altitude/elevation over terrain; cloud base AGL vs AMSL; live ft/m and NM/km converter. Shared: height-datums
- 2.5 Basic physics (8d 0w): tip-to-tail vector addition (drag the vectors); KE grows with V²; zoom climb; forces in a climb/glide with a path-angle slider. Shared: energy-trade
- 3.1 Piston engine aircraft (11d 0w): four-stroke over two crank turns (crank slider); leaning → RPM/EGT/power; electrical current with an alternator-failure toggle; carburettor venturi and butterfly with a throttle slider; power vs altitude. Shared: mixture-leaning, power-vs-altitude. +existing density-height
- 3.2 Fuels and oils (4d 0w): condensation overnight, part-full vs full tank (time-lapse); water settling to the sump and drain; fuel-sample colour check
- 3.3 Engine handling (5d 0w): detonation vs normal flame front; magneto check L/R/BOTH → RPM drop; CHT during a long idle descent (shock cooling); gauges reacting to scenarios. Shared: detonation-chamber, mixture-leaning
- 3.4 Malfunctions (8d 0w): carb-ice risk from OAT and dew point; ice building while you chase the RPM; carb heat check; vapour lock on a hot restart. Shared: carb-ice-risk, carb-ice-build
- 3.5 Flight instruments (10d 1w): pitot/static blockage simulator; gyro rigidity and precession; DI drift and reset; ASI needle across the arcs. Shared: pitot-static-sim, asi-arcs-explorer, gyro-precession-3d, compass-turning-errors
- 4.1 Basic aerodynamics (8d 1w): centre of pressure with AoA; airflow separating toward the stall; four forces balancing as power or attitude changes; energy trade. Shared: lift-curve-flap, energy-trade
- 4.2 Lift and drag (5d 0w): lift formula sliders; drag curves; CL vs AoA; downwash and tip vortices. Shared: drag-curve-explorer [x], lift-curve-flap
- 4.3 Climbing (5d 0w): ROC vs airspeed with Vx/Vy; climb gradient over the ground with wind; ROC and GS → ft/NM, %, degrees. Shared: climb-performance, climb-gradient-wind
- 4.4 Wake turbulence (4d 0w): vortices sinking and spreading; crosswind parking the upwind vortex; your path above or beyond the wake; strength vs heavy/clean/slow. Shared: wake-vortices-3d
- 4.5 Thrust stream turbulence (4d 0w): jet blast length vs idle/breakaway/take-off power; breakaway thrust sweeping as a jet turns; rotor downwash; a safe hold position
- 5.1 Charts (4d 0w): the same area across WAC/VNC/VTC scales (zoom); layer tints and contours lifted into 3D terrain. Shared: airspace-3d
- 5.2 Documentation (5d 0w): PRD hours in UTC vs local; ERSA entry with hover-to-explain blocks; airspace-active check as a clickable decision. Shared: utc-local-clock
- 6.1 Airworthiness and equipment (4d 0w): MR validity; defect endorsement stepper. Shared: maintenance-release-check
- 6.2 Take-off and landing performance (5d 3w): slope slider → TODR/LDR; factor stack toggles; ground effect and wind shear on take-off. Shared: takeoff-factor-stack, weight-limits-governs, ground-effect-height, climb-gradient-wind, wind-gradient-approach
- 6.3 Speed limitations (7d 1w): V-n with weight moving VA; gust load vs airspeed; spin vs spiral dive; flap speeds on a moving ASI. Shared: v-n-envelope, asi-arcs-explorer, spin-vs-spiral-3d
- 6.4 Weight and balance (4d 1w): CG slider → tail download, stall speed, stability; seesaw moments with draggable weights

### GNSSC
- 2.1 GNSS operation (5d 0w): trilateration spheres; satellite geometry/DOP (drag satellites → error area); RAIM; waypoint passage TO/FROM and CDI. Shared: gnss-trilateration-3d, vor-cdi. +existing wind-triangle

### PAKA
- 2.1 Propellers (3d 1w): constant-speed governor (airspeed → blade pitch, RPM held, flyweights); fixed-pitch overspeed in a dive; blade twist along the span
- 2.2 Aircraft systems (6d 0w): stagnation point moving with AoA to trigger the stall warning; autopilot loop correcting a disturbance; auto-trim fighting the pilot. Shared: lift-curve-flap
- 3.1 Take-off and landing performance (8d 3w): stacked factors; weight limits; wind gradient on final; ground-effect float. Shared: takeoff-factor-stack, weight-limits-governs, wind-gradient-approach, ground-effect-height, power-vs-altitude, climb-gradient-wind

### PAKC
- 2.1 Piston engines (PPL) (4d 1w): full throttle height; mixture richening with altitude; NA vs turbo power. Shared: power-vs-altitude, mixture-leaning, detonation-chamber
- 2.2 Supercharging (2d 0w): wastegate holding boost to the critical altitude; turbo vs gear-driven compressor flow; overboost on a cold day; intercooler. Shared: power-vs-altitude, detonation-chamber
- 2.3 Flight instruments (PPL) (5d 2w): SH compass turning/acceleration errors; IAS→TAS; pitot-static blockage; alternate static. Shared: compass-turning-errors, airspeed-chain, pitot-static-sim, heading-converter, gyro-precession-3d
- 3.1 Operation of radio systems (2d 0w): clipped transmission (PTT vs speech timeline); readability scale; UTC/WST. Shared: utc-local-clock. Text-heavy: static diagrams
- 3.2 Pre-flight radio test (2d 0w): squelch threshold vs noise and signal (slider); volume/squelch set-up on a radio face. Text-heavy
- 3.3 Fault finding (2d 0w): radio chain fault simulator (click a component, see the symptom); hiss test. Text-heavy
- 3.4 Position reporting in the circuit (5d 1w): traffic picture built from CTAF calls; converging aircraft and the 10 NM call; overhead join. Shared: overhead-join-3d
- 3.5 Responsibilities of a radio operator (2d 0w): "may I transmit this?" scenario filter. Text-heavy: static diagrams
- 3.6 Radio system components (4d 0w): a call flowing through the chain with failure points; AM modulation (slider); antenna locations
- 3.7 Distress and emergency messages (4d 0w): MAYDAY vs PAN PAN sorter; distress message builder. Shared: sartime-phases
- 3.8 Radio failure procedures (3d 0w): tower light signals (animation); no-radio overhead join. Shared: overhead-join-3d, sartime-phases
- 3.9 Radiotelephone controls (2d 0w): COM radio active/standby flip; audio panel; transponder modes and codes. Text-heavy
- 3.10 Radio waves (4d 0w): VHF range vs height; HF skip zone vs frequency and time of day; wavelength/frequency slider; ground, sky and space waves. Shared: vhf-range-height

### PFRA
- 2.1 Documentation (6d 0w): AIRAC 28-day calendar; NOTAM validity in UTC vs your flight window; ERSA entry. Shared: utc-local-clock
- 2.2 Licences (4d 0w): rolling recency windows; classification of operations tree. Shared: recency-window
- 2.3 Flight rules (5d 0w): PRD activation in UTC vs local; usable area on an unsealed aerodrome. Shared: utc-local-clock
- 2.4 Air service operations (6d 0w): TAF arrival window; over-water gliding distance vs height (Rottnest); TEMPO/INTER → holding fuel. Shared: taf-arrival-check [x], okta-sky. +existing glide-range-vs-wind
- 2.5 Aerodromes (7d 1w): displaced threshold distances; ground signals and windsock; overhead join. Shared: declared-distances-runway, overhead-join-3d
- 2.6 Airspace and altimetry (9d 1w): Perth airspace in 3D; transition altitude/layer with a QNH slider; navigation tolerance vs CTA boundary; VFR cruising levels. Shared: airspace-3d, cruising-level-by-track, vmc-minima-picker, height-datums
- 2.7 Emergencies, accidents and incidents (5d 0w): mercy-flight and accident/incident sorters; transponder codes. Text-heavy
- 2.8 Security (5d 0w): ADIZ entry tolerance (drag entry point and time); interception signals (animation)
- 2.9 Emergencies and SAR (6d 0w): SAR phases from SARTIME; lights meanings. Shared: sartime-phases

### PHFC
- 2.1 Basic health (5d 0w): stress-performance; ear equalisation; oxygen chain. Shared: stress-performance, ear-equalisation, oxygen-chain, alcohol-timeline
- 2.2 Health and fitness (4d 0w): blood-alcohol curve with drinks and finish time; hangover past zero BAC. Shared: alcohol-timeline, oxygen-chain
- 2.3 Hyperventilation (5d 0w): breathing → CO2 → symptoms vicious circle (animation); hypoxia vs hyperventilation symptoms with altitude. Shared: altitude-oxygen, stress-performance
- 2.4 Atmospheric pressure changes (5d 0w): Boyle's law gas volume vs altitude (balloon, gut, ear); dive depth and time → wait before flying. Shared: ear-equalisation, altitude-oxygen
- 2.5 Anatomy of the ear (5d 0w): canal fluid lag; noise → safe exposure time; speech masked by cabin noise. Shared: canal-lag-turn, noise-dose, ear-equalisation
- 2.6 Hearing protection (4d 0w): noise dose; ANR anti-phase cancellation (animation); passive vs ANR by frequency. Shared: noise-dose
- 2.7 Vision and illusions (9d 0w): constant-bearing collision (target fixed then blossoming); dark adaptation over 30 min; graveyard spiral; runway slope/width illusions → wrong glidepath (slider). Shared: canal-lag-turn, clock-code-bearing
- 2.8 Motion sickness (3d 0w): sensory conflict (animation); symptom progression. Shared: canal-lag-turn
- 2.9 Acceleration (5d 1w): g → blood at eye level, greyout to G-LOC; vision narrowing; negative g. Shared: g-load-effects, spin-vs-spiral-3d
- 2.10 Toxic hazards (4d 0w): CO ppm × time → COHb% → symptoms; CO plus altitude; exhaust leak into the cabin heater (animation). Shared: oxygen-chain, altitude-oxygen
- 2.11 The atmosphere (5d 0w): O2 partial pressure; saturation curve; gas exchange (animation). Shared: altitude-oxygen, oxygen-chain
- 2.12 Hypoxia (6d 0w): TUC vs altitude; stages by cabin altitude; night vision loss with altitude. Shared: altitude-oxygen, oxygen-chain
- 2.13 Human factors considerations (4d 0w): information processing with an attention bottleneck (animation); DECIDE stepper. Shared: stress-performance
- 2.14 First aid and survival (3d 0w): DRSABCD stepper; ground-to-air codes seen from the air. Text-heavy
- 2.15 Threat and error management (3d 0w): threat → error → undesired state chain with trap points (interactive scenario). Shared: stress-performance

### PMTC
- 2.1 Composition of the atmosphere (2d 0w): ISA lapse to the tropopause (altitude slider); pressure halving with height; tropopause height by latitude. Shared: altitude-oxygen
- 2.2 Heat, temperature, pressure, humidity (2d 3w): radiation inversion overnight; relative humidity from T and Td; conduction/convection/radiation. Shared: overnight-cooling, cloud-base-from-spread
- 2.3 Clouds and precipitation (8d 0w): cumulus base from the spread; five lifting mechanisms (animations); ten genera; oktas. Shared: cloud-base-from-spread, okta-sky, cloud-genera-3d, thunderstorm-stages, sea-breeze-day. +existing lapse-rate-stability
- 2.4 Visibility (5d 0w): radiation fog forming and burning off; advection fog on an onshore flow; slant vs horizontal visibility. Shared: overnight-cooling, vmc-minima-picker, taf-arrival-check
- 2.5 Winds (4d 0w): pressure gradient + Coriolis → geostrophic wind (SH); friction backing with descent; diurnal variation. Shared: pressure-systems-wind, sea-breeze-day, overnight-cooling, wind-gradient-approach
- 2.6 Air masses and fronts (8d 0w): cold front passing a station (time-lapse); wave depression → occlusion; west coast trough position → Perth wind; tropical cyclone. Shared: thunderstorm-stages, sea-breeze-day. +existing lapse-rate-stability
- 2.7 Flight considerations (11d 0w): mountain wave vs wind speed; icing type vs temperature and droplet size; microburst; thunderstorm life cycle. Shared: scarp-wave-and-rotor, thunderstorm-stages, carb-ice-risk, wind-gradient-approach, vmc-minima-picker, mountain-wave-3d

### PNVC
- 2.1 Form of the earth, direction (7d 0w): lat/long on a globe; great circle vs rhumb line; MH + RB = MB; variation and deviation. Shared: heading-converter, clock-code-bearing. +existing wind-triangle
- 2.2 Time (2d 0w): longitude → arc to time → LMT; daylight graph reading; civil twilight with the sun 6° below the horizon; summer-time zones. Shared: utc-local-clock
- 2.3 Charts and documents (8d 0w): terrain-safe altitude from tints and spot heights; orienting the chart to track; scale arithmetic; airspace section. Shared: airspace-3d, heading-converter
- 2.4 Computation techniques (4d 3w): TAS from IAS, pressure height and temperature; TOC/TOD placement; time-distance-speed; climb gradient vs wind. Shared: airspeed-chain, climb-gradient-wind, heading-converter
- 2.5 Pilot navigation (4d 1w): fix quality from position-line crossing angle (drag the lines); DR position building over time; revising ETA from a groundspeed check. +existing wind-triangle
- 2.6 Radio navigation aids (6d 0w): VOR OBS/CDI and TO/FROM; ADF RB → MB; NDB errors (animations); DME slant range. Shared: vor-cdi, clock-code-bearing, vhf-range-height
- 2.7 Area navigation (3d 0w): VOR/DME waypoint error growing with distance; drift and update snap; GNSS CDI. Shared: vor-cdi. +existing wind-triangle

### POPA
- 2.1 Aerodromes and ALAs (8d 1w): TODR/TODA/LDR/LDA on a runway; 1-in-20 obstacle surface (drag an obstacle); take-off path to 50 ft. Shared: declared-distances-runway, takeoff-factor-stack, climb-gradient-wind
- 2.2 Take-off and landing performance (12d 2w): stacked factors; climb weight limit vs MTOW; 10% overweight cascade; wind shear and ground effect. Shared: takeoff-factor-stack, weight-limits-governs, wind-gradient-approach, ground-effect-height, energy-trade, power-vs-altitude, height-datums
- 2.3 Density height (3d 2w): reading a density altitude chart (draggable crosshair). Shared: power-vs-altitude
- 2.4 Performance charts (4d 1w): take-off weight chart walkthrough (drag a line through the panels); landing weight capping take-off weight; interpolation. Shared: weight-limits-governs, takeoff-factor-stack
- 2.5 Climb, cruise and descent (9d 0w): climb table subtract/interpolate; TOD from altitude, GS and ROD; power-required curve; leaning vs fuel flow. Shared: drag-curve-explorer [x], climb-performance, mixture-leaning, power-vs-altitude

### POPC
- 2.1 Loading (5d 1w): floor loading (board size → kg/m²); weight ladder ramp to landing; graphical loading system. Shared: weight-limits-governs
- 2.2 Speed limitations (8d 1w): V-n; gust load; spin vs spiral; flap limits. Shared: v-n-envelope, asi-arcs-explorer, spin-vs-spiral-3d
- 2.3 Using ERSA (6d 1w): declared distances; PRD UTC→WST; choosing the runway from the wind. Shared: declared-distances-runway, utc-local-clock, takeoff-factor-stack. +existing crosswind-component
- 2.4 Flight plan preparation (8d 0w): TAF window; fuel plan builder; alternate vs holding decision. Shared: taf-arrival-check [x], sartime-phases
- 2.5 Completing a VFR flight plan (7d 1w): route side profile under CTA steps and terrain; cruising level from track; latest departure vs last light. Shared: airspace-3d, cruising-level-by-track, utc-local-clock, taf-arrival-check. +existing wind-triangle, crosswind-component
- 2.6 ETP, PNR and diversions (6d 0w): ETP sliding into wind (wind slider on a route line); PNR vs endurance and wind; diversion options vs reserve. Shared: taf-arrival-check
- 2.7 Airworthiness and equipment (4d 0w): equipment required by flight type; MR validity. Shared: maintenance-release-check

### RBKA
- 2.1 Piston engine (6d 0w): leaning by RPM; carb ice building and chasing the RPM; carb heat response. Shared: mixture-leaning, carb-ice-risk, carb-ice-build, detonation-chamber
- 3.1 Lift and drag (8d 1w): CL and L/D vs AoA; weight → stall and best glide speeds; flap effect; ground effect. Shared: drag-curve-explorer [x], lift-curve-flap, ground-effect-height
- 3.2 Flight controls (6d 1w): adverse yaw and the rudder fix (animation); control effectiveness vs airspeed and slipstream; trim tab holding the elevator; flap pitch change. Shared: lift-curve-flap, asi-arcs-explorer
- 3.3 Climbing (7d 1w): excess thrust/power → Vx/Vy; weight, altitude and flap; wind shear on climb-out; climb gradient with wind. Shared: climb-performance, climb-gradient-wind, wind-gradient-approach, power-vs-altitude. +existing density-height
- 3.4 Descents (7d 1w): power and flap at constant IAS → descent angle; glide speed off best L/D; weight. Shared: drag-curve-explorer [x], energy-trade
- 3.5 Turning (4d 2w): turn radius/rate vs bank and TAS (top view); overbanking tendency (animation); low-level downwind turn illusion. Shared: g-load-effects
- 3.6 Stalling, spinning, spiral dives (7d 2w): wing drop and aileron raising local AoA (animation); spin vs spiral; wind shear toward the stall. Shared: spin-vs-spiral-3d, lift-curve-flap, wind-gradient-approach
- 3.7 Taxi, take-off, landing (8d 1w): crosswind taxi control positions (rotate the wind); wheelbarrowing (animation); crab vs wing-down; wind gradient on final. Shared: crosswind-landing-3d, wind-gradient-approach, ground-effect-height, energy-trade
- 3.8 Structural damage (7d 0w): V-n with weight moving VA; damaged leading edge; controllability check (animation). Shared: v-n-envelope
- 4.1 Take-off and landing performance (5d 1w): slope → retarding force; slush drag vs thrust; combined distances. Shared: takeoff-factor-stack
- 4.2 Flap speeds (6d 0w): flap load vs V² above VFE; staged flap retraction on the go-around (animation); ASI arcs. Shared: asi-arcs-explorer, lift-curve-flap

### RFRC
- 2.1 Documentation (4d 0w): MR validity; document hierarchy. Shared: maintenance-release-check. Text-heavy
- 2.2 Licence privileges (6d 0w): recency windows; tighter-limit-applies comparator. Shared: recency-window. Text-heavy
- 2.3 Conditions of flight (9d 0w): right of way converging/head-on/overtaking (animation); take-off separation behind a preceding aircraft (animation); minimum heights (3D); VMC by class. Shared: vmc-minima-picker, cruising-level-by-track, minimum-heights-3d, airspace-3d, alcohol-timeline. +existing altimeter-subscale
- 2.4 Air service operations (5d 0w): refuelling safety zone; seat belts across flight phases (timeline)
- 2.5 Aerodromes (6d 1w): overhead join; windsock reading (wind slider); taxiway signs and holding points. Shared: overhead-join-3d. +existing crosswind-component
- 2.6 Airspace (7d 0w): Perth airspace in 3D; Class D reverting when the tower closes (time slider); PRD activity. Shared: airspace-3d, utc-local-clock
- 2.7 Emergencies and SAR (5d 0w): SARTIME phases; flashing-light signals (animation). Shared: sartime-phases

### RMTC
- 2.1 Local weather (10d 0w): sea breeze [x]; radiation fog overnight; thunderstorm life cycle; summer/winter pressure pattern. Shared: sea-breeze-day [x], overnight-cooling, thunderstorm-stages, scarp-wave-and-rotor, pressure-systems-wind, cloud-base-from-spread. +existing lapse-rate-stability
- 2.2 Forecasts and reports (6d 0w): TAF window [x]; TAF/METAR hover decoder; GAF AMSL vs TAF AGL. Shared: taf-arrival-check [x], okta-sky, height-datums. +existing altimeter-subscale
- 2.3 Significance of observations (9d 0w): wind gradient → IAS loss; microburst; nocturnal low-level jet and dawn shear; dust devil. Shared: wind-gradient-approach, overnight-cooling, thunderstorm-stages, scarp-wave-and-rotor, sea-breeze-day
