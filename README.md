# CPSC 69100 Fall 2024

## Datapunk

### Requirements Document

---

**Ethan Epperson-Jones / **[distracted.e421@gmail.com](mailto\:distracted.e421@gmail.com)**

**Date submitted:** 10/6/24

---

### Introduction (3 points)

- The goal of this project is to **empower users to reclaim the data that large corporations collect and profit from**, allowing them to gain insights and control over their personal information. This will be done by providing users with a platform to import, analyze, visualize, and leverage their own data. Unlike the data analysis systems used by corporations, Datapunk is user-centric, meaning the user has full control over what is analyzed and how it is used.

  - **User-Controlled Analysis**: Datapunk will allow users to define their own metrics and parameters for data analysis, rather than relying on predefined corporate algorithms. Users will be able to customize the insights they generate, ensuring that the analysis is relevant to their personal goals. For instance, a user interested in understanding their digital habits can set specific parameters to see how often they interact with different types of content or how their usage patterns change over time.
  - **Transparent Data Processing**: Unlike corporate systems that are often black boxes, Datapunk will provide transparency into how the data is processed and analyzed. Users will be able to see exactly which algorithms are used, adjust them, or even replace them with their own. This ensures that there are no hidden motives or unintended biases in the analysis.
  - **Focus on Personal Empowerment**: The platform will include tools that help users derive insights for self-improvement, such as identifying time sinks, evaluating their communication patterns, or understanding their physical movement habits. These insights are tailored for personal growth rather than for optimizing ad targeting or monetization, as is common in corporate data systems.

- The reason this project is important is because \*\*modern data practices are often exploitative, focusing on how companies can extract value from users without returning the benefits. Unlike major tech corporations like Google, Microsoft, and Amazon, which use data for targeted advertising, behavioral tracking, and monetization without meaningful user consent, Datapunk is built around transparency and user empowerment.

  - **User-Centric Ownership**: With Datapunk, users maintain complete ownership of their data and control over how it is processed and used. For example, rather than aggregating data to sell targeted ads, Datapunk empowers users to gain personal insights that directly benefit them—such as identifying unhealthy usage patterns or finding opportunities to save time.
  - **No Hidden Monetization**: Unlike major corporations that monetize user data through advertising and partnerships, Datapunk's focus is solely on providing value to the user without any form of hidden monetization or third-party data sharing. Users are never the product; their data is theirs alone.
  - **Full Transparency and Customization**: The data analysis methods used by Datapunk are open and modifiable, providing full transparency. Users can view, adjust, or replace any analysis algorithm according to their personal preferences. This level of transparency is fundamentally different from corporate systems, where the inner workings are often proprietary and opaque to the user.
  - **Privacy-First Analysis**: Datapunk uses privacy-first methodologies, meaning that all data processing happens locally or on user-controlled storage, ensuring that no personal data is uploaded to centralized servers without explicit permission. This contrasts with companies like Google and Amazon, which aggregate user data centrally to extract insights at the expense of privacy.

- The beneficiaries of this project are **individual users who want to take control of their personal data**, including **privacy advocates, tech-savvy individuals interested in the quantified self movement, and people curious about how they are profiled by tech giants**. It also has potential applications for **small organizations** that want an in-house way to manage and leverage data without external interference or data privacy risks.
  - **Neurodivergent and Tech-Savvy Individuals**: Datapunk is particularly well-suited for neurodivergent individuals, such as those with ADHD or autism, who benefit from structure, visualization, and tools that provide actionable insights into their habits and routines. By making data accessible and customizable, Datapunk helps users better understand their behaviors and make adjustments to improve productivity, well-being, and overall mental health.
  - **Team and Organizational Data Empowerment**: For small organizations and teams, Datapunk offers a unique opportunity to leverage data collaboratively, without sacrificing privacy or control. Teams can import and analyze data to optimize workflows, understand communication patterns, and identify potential inefficiencies—all while ensuring that sensitive internal data is not shared with third-party entities. This makes it particularly valuable for non-profits, startups, and community organizations that need robust data capabilities without the overhead or risk of using major tech platforms.

---

### Features (10 points)

The final product will offer the following features:

#### Data Import and Parsing

- **Custom Data Import Tools**: Users will be able to import their personal data from various sources, such as Google Takeout, Microsoft exports, social media archives, and other digital platforms. The data import tools will support multiple file formats (JSON, CSV, XML, etc.) and will automate data parsing into structured forms that can be analyzed or visualized.
- **Data Parser**: Datapunk will automatically parse these files into specific data categories such as locations, communication logs, search history, and more, allowing users to understand the scope and content of the data that companies hold on them.

#### Secure Storage and Encryption

- **End-to-End Data Encryption**: All imported data will be encrypted both at rest and in transit. We will leverage robust, well-established encryption libraries to protect user privacy. No data will leave the user's local storage without explicit permission, emphasizing control and data security.
- **User-Controlled Storage**: Users will be able to choose where their data is stored—whether locally, on a personal server, or in a cloud storage solution—giving flexibility according to user comfort and security requirements.

#### Data Visualization Dashboard

- **Interactive Visualizations**: Datapunk will include a customizable dashboard where users can visualize different aspects of their data. These visualizations will include **timeline charts**, **geolocation maps**, **activity graphs**, and **relationship networks**. The goal is to make large datasets easy to understand and explore, helping users identify patterns, trends, and anomalies in their behavior.
- **Customizable Insights**: Users can create and save custom visualizations or queries to understand specific parts of their data. For example, they might visualize how their movement patterns have changed over time, or see an overview of their interactions with certain people or services.
- **User-Defined Metrics**: Users will have the option to define custom metrics for analysis. For example, a user could create a metric to measure the time spent on different categories of activities, such as work, leisure, or exercise, allowing for highly personalized insights.

#### Data Export and API Integration

- **Data Export Tools**: Users will be able to export their parsed and enriched data in various formats. This allows them to make use of the data for other purposes, whether for research, integration into other software, or archiving purposes.
- **API Access**: A core feature will be the provision of **API endpoints** for accessing parsed data, allowing users or developers to integrate the data with other applications, automation tools, or personal projects. This will make Datapunk a central hub for personal data management that other tools can connect to.

#### Data Enrichment and AI Integration (Planned for Future)

- **Data Enrichment**: Datapunk will eventually offer basic enrichment options like clustering data into categories (e.g., travel, work, social) and summarizing trends. This might involve tagging data, providing context to different entries, and recognizing repeated patterns.
- **AI-Powered Recommendations**: In the long term, AI integration is envisioned to provide personalized recommendations based on the user's own data, such as habit improvement suggestions, potential time-saving patterns, or content curation—all controlled by the user, without external data exploitation.

---

### Production Needs (3 points)

Completing this project requires access to certain important resources. These include data, software, hardware, and financial needs, as described below:

#### Data

- The data needed includes user exports from Google, Microsoft, and potentially other tech platforms. These datasets will form the basis for parsing, analysis, and visualization.

#### Software

- The software development tools needed include **Python** for data processing, **Postgres or MongoDB** for data storage, and libraries for **data encryption** and **visualization**. The platform will also use **custom APIs** for integration with external tools.

#### Hardware

- Standard computing hardware should suffice, though **cloud-based infrastructure** could be useful for scalability or real-time data processing, depending on the project’s growth.

#### Funding

- Currently, no substantial financial needs are anticipated. However, if the project requires additional resources (e.g., cloud hosting or specific security tools), a small budget for cloud infrastructure could be justified.

---

### User Needs (3 points)

- The end users are going to be **privacy-conscious individuals and tech enthusiasts** who are interested in regaining control over their personal data and deriving insights from it.
- To effectively use the product of this work, the end users will need to be trained on how to **import their data, navigate the visualizations, and interpret the insights** the platform provides.
- To help the intended users benefit from this work, we will provide appropriate documentation. Documentation will include **user guides** on how to import data, **tutorials** on navigating visualizations, and **API integration instructions**.

---

### Security and Privacy (3 points)

- This project **does require access to personally identifiable information and private data**, as it processes and visualizes user data from tech giants like Google and Microsoft.
- The project will include appropriate controls to protect this data, including **data encryption** for storage, **secure APIs**, and **user authentication measures** to prevent unauthorized access.

---

### Summary (3 points)

- This project will produce **a platform that empowers users to reclaim and analyze their personal data** from large tech corporations.
- It will benefit **privacy-conscious individuals** by providing them features such as **data parsing, secure storage, data visualization, and API integration**.
- The project **does deal with people’s private data**, but it will include appropriate controls to protect it.
- To complete this project, we will make use of **Python, encryption libraries, data visualization tools, and possibly cloud infrastructure**. At this time, no specific funding is required, though cloud resources may necessitate a small budget if needed for scaling.
