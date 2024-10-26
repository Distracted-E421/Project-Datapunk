
# Getting Started with Svelte for Datapunk's Frontend

This guide walks you through setting up Svelte with SvelteKit to serve as the frontend for Datapunk. This setup is designed to let you focus on creating a responsive, interactive user interface, connecting to backend data endpoints as needed.

## 1. Setting Up SvelteKit

1. **Initialize the Project**
   ```bash
   npm create svelte@latest datapunk-frontend
   ```
   - Follow the prompts to choose **SvelteKit** and **TypeScript (optional)**.
   - Select "Skeleton Project" to start with a clean setup.

2. **Install Dependencies**
   ```bash
   cd datapunk-frontend
   npm install
   ```
   - This installs SvelteKit’s dependencies, including **Vite** for fast development and optimized builds.

3. **Start the Development Server**
   ```bash
   npm run dev -- --open
   ```
   - This launches the development server at `http://localhost:5173`.

## 2. Understanding SvelteKit Structure

SvelteKit organizes code using file-based routing. Here’s a brief layout:

```
/src
│
├── /routes         # Page routes for navigation
├── /lib            # Reusable components, stores, utilities
└── /assets         # Static files (images, icons, etc.)
```

- **`/routes`**: Each file corresponds to a route (e.g., `/routes/dashboard.svelte` maps to `/dashboard`).
- **`/lib`**: For reusable components, stores, and utilities.
- **`/assets`**: For images, icons, and static files.

## 3. Creating Basic Routes and Pages

1. **Define Main Pages**
   - Create main pages like **Dashboard**, **Settings**, and **Import**.
   
   ```markdown
   └── /src/routes
       ├── /dashboard.svelte      # Main dashboard page
       ├── /settings.svelte       # User settings page
       └── /import.svelte         # Data import/upload page
   ```

2. **Basic Dashboard Page Setup**
   - Create a simple component in `/src/routes/dashboard.svelte`:
   
   ```svelte
   <!-- dashboard.svelte -->
   <script>
     import Widget from '$lib/components/Widget.svelte';
   </script>

   <h1>Welcome to Datapunk Dashboard</h1>
   <Widget title="User Activity"/>
   ```

3. **Adding Navigation**
   - Create a `Navbar.svelte` component in `/lib/components`:
   
   ```svelte
   <!-- Navbar.svelte -->
   <nav>
     <a href="/dashboard">Dashboard</a>
     <a href="/import">Import</a>
     <a href="/settings">Settings</a>
   </nav>
   ```

   - Include this in each main page layout for consistent navigation.

## 4. Building Interactive Components

1. **Creating Widgets for the Dashboard**
   - Svelte components combine HTML, JavaScript, and CSS in a single file, making each widget self-contained.

   ```svelte
   <!-- Widget.svelte -->
   <script>
     export let title = "Widget Title";
   </script>

   <div class="widget">
     <h2>{title}</h2>
     <!-- Add interactive elements like charts or graphs here -->
   </div>

   <style>
     .widget { padding: 1rem; border: 1px solid #ccc; }
   </style>
   ```

2. **Adding Interactivity with Reactive Variables**
   - Use Svelte’s reactivity for dynamic data updates.
   
   ```svelte
   <!-- InteractiveWidget.svelte -->
   <script>
     let count = 0;
     function increment() { count += 1; }
   </script>

   <div>
     <p>Count: {count}</p>
     <button on:click={increment}>Increase Count</button>
   </div>
   ```

## 5. Managing State with Svelte Stores

1. **Setting up a Store for Global State**
   - Stores provide reactive global state without the need for Redux.

   ```javascript
   // src/lib/stores.js
   import { writable } from 'svelte/store';

   export const userSettings = writable({
     theme: 'dark',
     layout: 'grid'
   });
   ```

2. **Using the Store in Components**
   - Access the store in any component:
   
   ```svelte
   <script>
     import { userSettings } from '$lib/stores';
     let settings;
     $: settings = $userSettings;
   </script>

   <p>Current theme: {settings.theme}</p>
   ```

## 6. Fetching Data from Backend Endpoints

SvelteKit simplifies data fetching by allowing you to use `load` functions in routes.

1. **Creating a Data Endpoint**
   - Create an API route in `/src/routes/api/data.js`:

   ```javascript
   // api/data.js
   export async function get() {
     const data = await fetchDataFromBackend();
     return { body: { data } };
   }
   ```

2. **Using the `load` Function in Pages**
   - Use `load` to fetch data before rendering the page:

   ```svelte
   <!-- dashboard.svelte -->
   <script context="module">
     export async function load() {
       const res = await fetch('/api/data');
       const data = await res.json();
       return { props: { data } };
     }
   </script>

   <script>
     export let data;
   </script>

   <div>Data fetched: {JSON.stringify(data)}</div>
   ```

## 7. Styling with TailwindCSS

1. **Install TailwindCSS**
   ```bash
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

2. **Configure TailwindCSS**
   - Add Tailwind to your project by updating your `tailwind.config.js` file.

   ```javascript
   // tailwind.config.js
   module.exports = {
     content: ['./src/**/*.{html,js,svelte,ts}'],
     theme: { extend: {} },
     plugins: [],
   };
   ```

3. **Import Tailwind Styles**
   - Add Tailwind’s base styles to your main CSS file:

   ```css
   /* src/app.css */
   @tailwind base;
   @tailwind components;
   @tailwind utilities;
   ```

   - Import `app.css` in `src/app.html` or in the main layout component.

## 8. Building and Deploying the App

1. **Build the Project for Production**
   ```bash
   npm run build
   ```

2. **Preview the Build**
   ```bash
   npm run preview
   ```

3. **Deploy to Vercel, Netlify, or Custom Server**
   - For Vercel:
     ```bash
     vercel --prod
     ```

   - For other platforms, follow their specific deployment instructions.

---

This setup will get you started with SvelteKit for building a frontend that’s interactive, fast, and easy to extend. With these basics in place, you can start connecting more complex backend data and refining the UI for Datapunk.
```