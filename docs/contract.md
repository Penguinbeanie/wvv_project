

### Conceptual Data Contract: WVV Mobility Data Platform

#### 1. Purpose
This data contract defines the semantic, structural, and quality guarantees provided by the data engineering pipeline to downstream consumers. The pipeline guarantees a unified, join-ready, with SQL queryable Database consisting of planned schedules (Target), observed operations (Actual), and external context.

---

#### 2. Core Data Entities & Granularity

| Conceptual Entity | Description | Granularity |
|---|---|---|
| **Target Schedule** *(Soll)* | Planned timetables combining 2022–mid-2026 GTFS feeds and 2026 PDF-extracted schedules. | One record per scheduled stop event |
| **Actual Operations** *(Ist)* | Stop-level telemetry (2022–2026).| One record per observed stop event |
| **Context** | Unified calendar of public/school holidays, university lecture periods, city events, weather, and pedestrian traffic. | One record per date-hour |
| **Stations & Lines** *(Reference)* | Central directory of stops (with coordinates) and transit routes (with mode/type). | One record per station / line |

---

#### 3. Producer Guarantees to Downstream Consumers

1. **Unified Identity Across Stops and Lines**

2. **Stable Trip Linkage via Fingerprinting**
    - Using StopIDs, Date, Time, Line, Start- and End-Stops.
3. **Temporal & Timezone Consistency**
   - All timestamps across all datasets are normalized to local time.
4. **Schema & Semantic Stability**
   - Downstream consumers see one stable schema across all years (2022–2026).
5. **Clean Context Mapping to the Rest of the Data via Date- and Timestamps**

---

#### 4. Consumer Join Contract
Under these guarantees, downstream consumers only need three conceptual relationships to combine the entire ecosystem:
* **Planned vs. Actual:** Join on **`(Date, Trip Fingerprint, StopID)`**.
* **Operations vs. Context:** Join on **`(Service Date, Hour)`**.
