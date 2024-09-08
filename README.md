# Datapunk: Project Overview

**Datapunk** is an open-source, privacy-focused tool that empowers users to reclaim, organize, and analyze personal data exported through services like Google Takeout. The project is designed to give users meaningful insights into their digital footprint without relying on corporate cloud services. By integrating open-source technologies like MongoDB, PostgreSQL (with PostGIS), and future Redis caching, Datapunk offers a flexible and scalable solution for personal data management.

## Data Parsing and Alignment

Datapunk will parse, clean, and store data from Google Takeout exports. The primary data formats are **JSON** and **CSV**. Data will be parsed based on its type and then routed to the appropriate database for storage and further processing.

### 1. Parsing JSON/CSV Data
- **JSON Parsing**: Using Python's built-in `json` module for small files or `ijson` for large files. This will handle semi-structured data like search history or location data.
- **CSV Parsing**: Using the `pandas` library for tabular data like app usage and media consumption.

### 2. Storing Parsed Data
Once parsed, the data will be stored based on its type:
- **MongoDB**: Semi-structured data like search history, app usage, and media history will be inserted into MongoDB collections. This allows for flexible document-based storage.
- **PostgreSQL with PostGIS**: GeoJSON data (e.g., location history) will be stored in PostgreSQL with PostGIS for geospatial indexing and querying.

### 3. Temporal and Geospatial Alignment
To derive meaningful insights, data from MongoDB (e.g., search history) will be aligned with data from PostgreSQL (e.g., location history) based on **time** and **location**. The following strategies will be used:
- **Temporal Alignment**: Align searches or media activity with location data using a sliding window approach, where data points within a specific time frame are considered related.
- **Geospatial Alignment**: Use PostGIS to find location data points near specific coordinates (e.g., searches made while at a particular location).

## Data Storage and Organization

Datapunk will use the following databases to handle different types of data:

### 1. MongoDB (Document-based storage)
- **Data Type**: Semi-structured or unstructured data.
- **Purpose**: Flexible storage for the variety of datasets exported by Google Takeout, such as search history, app usage, and media consumption.
- **Data Examples**:
  - Search history: Queries, timestamps, URLs.
  - Media history: YouTube watch history, content details.
  - App usage: App names, session times, durations.

### 2. PostgreSQL + PostGIS (Geospatial storage)
- **Data Type**: GeoJSON and spatial data.
- **Purpose**: Efficiently store and manage geospatial data such as location history, and allow for advanced geospatial queries.
- **Data Examples**:
  - Location history: Latitude, longitude, timestamps.
  - Places visited: GeoJSON data for geographic features.

### 3. Redis (Future Integration)
- **Data Type**: Frequently accessed or intermediate data (cached results).
- **Purpose**: Redis will be used for caching queries, storing frequent searches, and accelerating AI or data-heavy operations.
- **Planned Use Cases**:
  - Caching frequent geospatial queries (e.g., recent searches within a given area).
  - Storing intermediate results for real-time data analysis and AI-driven recommendations.

## Phase 3: Data Visualization & Insight Generation

In this phase, Datapunk provides real value to users by offering intuitive visualizations of their personal data. The visualizations will allow users to explore their data interactively, enabling them to gain insights into various aspects of their digital footprint. This phase will focus on creating a user-friendly, dynamic dashboard that presents data in meaningful and actionable ways.

### Visualizations

The following visualizations will be implemented to give users a comprehensive view of their personal data:

### 1. **Location History**
- **Visualization**: Map-based visualizations showing a user's travel history. Heatmaps will highlight frequently visited locations, and users will be able to filter locations by time ranges or specific geographies.
- **Technology**: Integration with mapping libraries such as **Leaflet** or **Mapbox** will allow for interactive map rendering, while **PostGIS** will provide the spatial data for these visualizations.
- **Features**:
  - Show movement patterns over time, displaying how the user's location changes on a map.
  - Generate heatmaps for frequently visited locations, highlighting areas where the user spends the most time.

### 2. **Search Trends**
- **Visualization**: Time-series graphs that visualize search queries over time, helping users identify patterns, peaks, or changes in behavior. The user will be able to see the frequency of search terms or types of searches made during specific periods.
- **Technology**: Use of **Plotly**, **D3.js**, or **Chart.js** for dynamic time-series visualization.
- **Features**:
  - Filter searches by time (e.g., past day, week, month).
  - Group searches by topics or keywords to identify recurring interests or trends.

### 3. **YouTube/Media Consumption**
- **Visualization**: Charts showing media consumption patterns over time, broken down by day, genre, or activity. Users can track their viewing habits, such as most-watched categories or the time of day they typically consume media.
- **Technology**: **Bar charts** and **pie charts** using **Plotly** or **D3.js** to display categorized data.
- **Features**:
  - View consumption trends based on genres, video length, or time of day.
  - Identify favorite categories of media or the hours during which the user consumes the most content.

### 4. **App Usage**
- **Visualization**: Line graphs or bar charts showing app usage over time, helping users identify their peak app usage hours, track the total time spent on different apps, and see which apps they use most frequently.
- **Technology**: **Plotly**, **D3.js**, or **Chart.js** for interactive visualizations.
- **Features**:
  - Filter app usage by date ranges to identify usage trends.
  - Visualize total time spent on each app, with breakdowns by day or session length.

### Dashboard

The dashboard will serve as the central hub where users can interact with their data. It will provide a range of filters and controls that allow users to customize their views, zoom in on specific data sets, and export insights.

- **User-friendly Interface**: The dashboard will be designed with simplicity in mind, offering a clean and intuitive interface that allows users to select different datasets (e.g., location history, search trends, app usage) and explore insights through visualizations.
- **Interactivity**: Users can filter data by time range, categories, or specific criteria (e.g., search queries containing certain keywords, media consumption from a specific genre).
- **Responsiveness**: Built using a modern JavaScript framework such as **React** or **Vue.js**, the dashboard will ensure smooth interactivity and responsive design across devices (desktop, tablet, mobile).
- **Customization**: Users can customize how the data is displayed, including switching between visualization types (bar charts, line graphs, heatmaps, etc.).

### Technologies

To ensure that the dashboard and visualizations are robust, responsive, and user-friendly, Datapunk will leverage the following technologies:

- **Frontend**: 
  - **HTML/CSS/JavaScript** for the foundational web structure and styling.
  - **React** or **Vue.js** to build the frontend and manage interactivity. These frameworks will enable the development of dynamic components that efficiently handle real-time data visualization.
  
- **Visualization Libraries**:
  - **Plotly**, **D3.js**, or **Chart.js** will be used to implement interactive, visually appealing charts and graphs.
  - **Leaflet** or **Mapbox** for handling map-based visualizations of location data.

- **Backend**: 
  - **Django** for managing the server-side logic, handling user authentication, data requests, and serving the required data to the frontend. Django will provide API endpoints that deliver parsed data to the frontend in real time for visualization.

### Key Features of the Dashboard
- **Data Filtering**: Users can filter by time range (e.g., last 7 days, last 30 days) and categories (e.g., search history, app usage, location data).
- **Exporting Insights**: Users can export visualized data or raw data as CSV or JSON for personal records or further analysis.
- **Real-Time Interaction**: Users can zoom in on specific data points, view detailed information on hover, and switch between different visualizations without reloading the page.


## Phase 4: Simplified Database Setup and Security

### 1. Local and Docker-Based Security Threats
- **Local System Risks**:
  - Unauthorized access to MongoDB or PostgreSQL running locally.
  - Snooping on the user's IP address, potentially exposing services that shouldn't be public.
  - Data theft from local files or databases if someone gains access to the machine.

- **Docker-Based Risks**:
  - Exposed container services (e.g., MongoDB, PostgreSQL ports) if Docker containers are not configured properly.
  - Weak security configurations within the Docker environment (e.g., no authentication, default settings).
  - Insecure Docker configurations that leave the host system vulnerable.

### 2. Securing MongoDB and PostgreSQL

#### MongoDB Security:
- **Authentication**: Enable authentication in MongoDB so that access to the database requires a username and password. Configure environment variables in Docker or use MongoDB config files for local setups.
- **Local Access Only**: Configure MongoDB to only bind to `localhost` or private IPs, ensuring it's not accessible from outside the host machine.
- **TLS Encryption**: Enable TLS/SSL encryption for all connections to MongoDB, ensuring that data is encrypted in transit.

#### PostgreSQL Security:
- **Authentication**: Ensure that PostgreSQL uses proper user roles and password-based authentication. Set up credentials through environment variables in Docker or configure `pg_hba.conf` locally.
- **SSL/TLS**: Enable SSL in PostgreSQL to encrypt communication between the app and the database.

### 3. Securing Access to Docker Containers
- **Network Isolation**: Use Docker’s internal network to keep database services (e.g., MongoDB, PostgreSQL) isolated from public networks. Only allow communication between containers.
- **Exposed Ports**: Limit exposed ports to only what’s necessary for services like the web app. Avoid exposing database ports to the public.
- **User Privileges**: Avoid running containers as root. Use non-root users for services like MongoDB and PostgreSQL to minimize the risk of privilege escalation.

### 4. Protecting Local Files and Data
- **Data Encryption**: Encrypt sensitive files (such as database backups) to ensure that even if someone accesses the user's local machine, the data cannot be easily read.
- **File Permissions**: Ensure that only authorized users can access the application’s data files and database directories.
- **Application Logs**: Avoid logging sensitive information like passwords, API keys, or personal data. Ensure logs are secured and accessible only by authorized users.
- **Backup Strategy**: If the app performs backups of databases, store these backups securely (either encrypted or with restricted access).

### 5. IP Address Protection and Network Security
- **Firewall Rules**: Set up firewall rules on the user’s local machine to restrict access to MongoDB and PostgreSQL ports, ensuring only local access.
- **VPN and IP Masking**: Recommend using a VPN to mask the user's IP when working on public or unsecured networks.
- **Network Security**: Provide tips for users to secure their local networks (e.g., enabling firewalls, avoiding public Wi-Fi).

### 6. Docker-Specific Security Best Practices
- **Limit Container Privileges**: Use Docker’s User Namespaces to map the container’s root user to a non-root user on the host, reducing the risk of host compromise.
- **Scan Images for Vulnerabilities**: Regularly scan Docker images (MongoDB, PostgreSQL, and your app) for vulnerabilities using tools like Clair or Anchore.
- **Resource Limits**: Set memory and CPU limits on containers to prevent resource exhaustion in case of a denial-of-service attack.

### Security Summary

#### For Docker:
1. **Database Security**:
   - Ensure MongoDB and PostgreSQL are configured with authentication and limited to internal Docker networks.
   - Use encryption (TLS/SSL) for data in transit.

2. **Network Security**:
   - Isolate Docker containers from external networks.
   - Only expose necessary services to external ports.

3. **Host Security**:
   - Restrict container privileges (use non-root users).
   - Ensure containers are scanned for vulnerabilities.

#### For Inno Setup (Local Deployment):
1. **Local Database Security**:
   - Ensure MongoDB and PostgreSQL are configured to use authentication and restricted to localhost.
   - Use file encryption and strict permissions to protect local data.

2. **Network and IP Protection**:
   - Recommend firewall rules to prevent external access to local services.
   - Encourage the use of VPNs or secure networks to protect user privacy.
