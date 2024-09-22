# **Datapunk: Project Overview**

**Datapunk** is an open-source, privacy-focused tool designed to empower users to reclaim, organize, and analyze personal data exported from services like Google Takeout. The project aims to give users meaningful insights into their digital footprint without relying on corporate cloud services. By integrating open-source technologies like **CouchDB**, **PostgreSQL (with PostGIS)**, and **future Redis caching**, Datapunk offers a flexible, scalable solution for personal data management and future AI integrations.

---

## **Data Parsing and Alignment**

Datapunk parses, cleans, and stores data from Google Takeout exports, supporting **JSON** and **CSV** formats. Data is parsed according to type and routed to the appropriate database for storage and processing, with **immediate analysis** applied for user insights right from the start.

### **1. Parsing JSON/CSV Data**

- **JSON Parsing**: Using Python’s `json` module for smaller files or `ijson` for large files, Datapunk handles semi-structured data like search history or location data.
- **CSV Parsing**: The `pandas` library processes tabular data like app usage and media consumption.

### **2. Storing Parsed Data**

Once parsed, data is stored based on its type:

- **CouchDB**: Document-based, semi-structured data like search history, app usage, and media history are stored in CouchDB, providing flexible, scalable storage.
- **PostgreSQL with PostGIS**: Geospatial data, such as location history, is stored in PostgreSQL with PostGIS, enabling advanced geospatial indexing and querying.

### **3. Temporal and Geospatial Alignment**

To derive meaningful insights, Datapunk aligns data across time and location:

- **Temporal Alignment**: Matches search or media activity to location data using a sliding time window.
- **Geospatial Alignment**: PostGIS queries are used to align activities based on proximity to specific locations, offering insights such as searches made at certain places.

---

## **Data Storage and Organization**

Datapunk uses multiple databases to manage various data types:

### **1. CouchDB (Document-based storage)**

- **Data Type**: Semi-structured or unstructured data.
- **Purpose**: Store flexible, scalable datasets such as search history, media usage, and app activity.
- **Data Examples**:
  - **Search history**: Queries, timestamps, URLs.
  - **Media history**: YouTube watch history, content details.
  - **App usage**: App names, session durations.

### **2. PostgreSQL + PostGIS (Geospatial storage)**

- **Data Type**: GeoJSON and spatial data.
- **Purpose**: Efficiently store and query geospatial data, including location history.
- **Data Examples**:
  - **Location history**: Latitude, longitude, timestamps.
  - **Places visited**: GeoJSON data for geographic features.

### **3. Redis (Future Integration)**

- **Data Type**: Frequently accessed or intermediate data (cached results).
- **Purpose**: Redis will be used for caching queries, storing frequent searches, and accelerating AI-driven recommendations.
- **Planned Use Cases**:
  - Caching frequent geospatial queries.
  - Storing intermediate results for real-time analysis.

---

## **Phase 3: Immediate Analysis & Insight Generation**

Datapunk immediately processes parsed data to offer valuable insights and visualizations through a dynamic user-friendly dashboard. This **immediate analysis** enriches user interaction with their personal data.

### **1. Summarization and Clustering**

- **Basic Summarization**: Instant stats, such as total searches or location points recorded, are generated immediately after parsing.
- **Clustering**: Search terms, locations, and media consumption patterns are grouped to reveal trends.

### **2. Pattern Recognition**

- **Temporal and Spatial Trends**: Datapunk identifies user behavior patterns, such as frequent search topics, peak app usage hours, or movement trends.
- **Outlier Detection**: Detects abnormal spikes in activity or deviations in location data.

---

## **Data Visualization & User Dashboard**

Datapunk’s dashboard allows users to interact with their personal data, offering customizable, real-time visualizations that can be filtered and exported.

### **Visualizations**

- **Location History**: Interactive maps show travel history, with heatmaps highlighting frequently visited areas. Powered by **Leaflet** or **Mapbox**.
- **Search Trends**: Time-series graphs visualize search frequency over time. Filters allow users to explore keyword patterns and peaks.
- **Media Consumption**: Charts display media usage trends, broken down by genre or time of day, using **Plotly** or **D3.js**.
- **App Usage**: Visualize app session times with bar or line graphs, showing peak usage periods.

### **Dashboard Features**

- **Interactivity**: Filters allow users to explore specific datasets, such as location history or media consumption, through dynamic controls.
- **Responsiveness**: The dashboard is built with **React** or **Vue.js**, ensuring smooth interactivity across devices.
- **Export Functionality**: Users can export visualized data as CSV or JSON for further analysis.

---

## **Phase 4: Data Security & Simplified Setup**

### **1. CouchDB & PostgreSQL Security**

- **Authentication**: CouchDB and PostgreSQL will require user authentication, with access limited to internal networks or local hosts.
- **Encryption**: TLS/SSL encryption for secure data transmission.

### **2. Docker Security**

- **Container Isolation**: Docker containers will use internal networking to ensure that database services are not publicly exposed.
- **User Privileges**: Containers will avoid root access, minimizing risks from privilege escalation.

### **3. Local System & IP Protection**

- **Data Encryption**: Local files, such as database backups, will be encrypted to prevent unauthorized access.
- **Network Security**: Firewall rules and VPN recommendations ensure users can protect their data when using public networks.

### **Security Summary**

- Datapunk’s deployment (via Docker or local) ensures secure database access, encrypted communication, and a strong focus on privacy.

---

### **Future Directions**

- **AI Integration**: In the future, Datapunk aims to integrate AI-driven recommendations and insights based on user data.
- **Cloud Scalability**: While designed for local deployment, Datapunk's architecture can scale to cloud-based environments with collaboration from frontend developers or cloud infrastructure specialists.