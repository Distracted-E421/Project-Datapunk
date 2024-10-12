**Datapunk Drag-and-Drop Interface Implementation Plan**

### **Overview**
The goal is to create a drag-and-drop interface that allows users to easily upload data files in a zipped format. This feature will simplify the data import process, making Datapunk more user-friendly and accessible to non-technical users. The plan will involve setting up both a backend service using FastAPI and a frontend interface using React.

### **Step 1: Backend Setup (FastAPI for File Handling)**

1. **Create a FastAPI Endpoint for File Uploads**
   - **Goal**: Set up an API endpoint to handle file uploads from the frontend. The backend will accept zip files, unzip them, and store the contents in a specified folder for further parsing.
   - **Tasks**:
     - Define an endpoint `/upload-data/` using FastAPI that accepts `POST` requests with file uploads.
     - Save the uploaded zip file temporarily, extract the contents, and remove the temporary file.
     - Trigger the appropriate parsing function after extraction.
   - **Example Code**:
     ```python
     from fastapi import FastAPI, File, UploadFile
     import shutil
     import zipfile
     import os

     app = FastAPI()

     @app.post("/upload-data/")
     async def upload_data(file: UploadFile = File(...)):
         data_dir = "data/"
         temp_file_path = os.path.join(data_dir, "temp.zip")

         # Save the uploaded file temporarily
         with open(temp_file_path, "wb") as buffer:
             shutil.copyfileobj(file.file, buffer)

         # Extract the zip file
         with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
             zip_ref.extractall(data_dir)

         # Remove the temporary zip file
         os.remove(temp_file_path)

         # Trigger the data parsing logic here
         # load_and_parse_data() or another function to parse the new files

         return {"status": "File uploaded and extracted successfully."}
     ```

2. **Dockerize FastAPI**
   - **Update Dockerfile**: Ensure the FastAPI dependencies are included and expose the necessary port (e.g., `8000`).
   - **Update docker-compose.yml**: Add the backend service to the `docker-compose.yml` file and expose the port to allow communication with the frontend.

### **Step 2: Frontend Setup (React for Drag-and-Drop Interface)**

1. **Initialize a React Project**
   - **Goal**: Create a new React project to serve as the user-facing part of the drag-and-drop data upload feature.
   - **Tasks**:
     - Use `create-react-app` to bootstrap the frontend.
     - Install `react-dropzone` to facilitate the drag-and-drop interaction.

   **Command to Bootstrap React Project**:
   ```bash
   npx create-react-app datapunk-frontend
   npm install react-dropzone
   ```

2. **Create Drag-and-Drop Component**
   - **Goal**: Develop a React component that allows users to drag and drop their data files.
   - **Tasks**:
     - Use the `react-dropzone` library to create a drop area where users can drag and drop their zip files.
     - Handle the uploaded file and send it to the FastAPI endpoint using a `POST` request.
   - **Example Code**:
     ```jsx
     import React from 'react';
     import { useDropzone } from 'react-dropzone';

     const FileUpload = () => {
       const onDrop = (acceptedFiles) => {
         const formData = new FormData();
         formData.append('file', acceptedFiles[0]);

         fetch('http://localhost:8000/upload-data/', {
           method: 'POST',
           body: formData,
         })
           .then((response) => response.json())
           .then((data) => {
             console.log(data);
             alert('File uploaded successfully!');
           })
           .catch((error) => {
             console.error('Error:', error);
             alert('Failed to upload file.');
           });
       };

       const { getRootProps, getInputProps } = useDropzone({ onDrop });

       return (
         <div {...getRootProps()} className="dropzone">
           <input {...getInputProps()} />
           <p>Drag 'n' drop some files here, or click to select files</p>
         </div>
       );
     };

     export default FileUpload;
     ```

3. **Add Styles for the Drag-and-Drop Component**
   - **Goal**: Make the drag-and-drop area visually appealing and easy to understand for users.
   - **Tasks**: Use CSS to style the drop area, indicating to users where they should drop their files.

4. **Run the Frontend**
   - **Command to Start React**:
   ```bash
   npm start
   ```

### **Step 3: Integration of Frontend and Backend**

1. **Enable CORS in FastAPI**
   - **Goal**: Allow the React frontend to communicate with the FastAPI backend without any cross-origin request issues.
   - **Tasks**: Add CORS middleware to the FastAPI app.
   - **Example Code**:
     ```python
     from fastapi.middleware.cors import CORSMiddleware

     app.add_middleware(
         CORSMiddleware,
         allow_origins=["http://localhost:3000"],  # React dev server
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```

2. **Docker Configuration**
   - **Update Docker Compose**: Update `docker-compose.yml` to include both the backend and frontend services.
   - **Ports**: Expose ports such as `8000` for FastAPI and `3000` for React to ensure they can communicate effectively.

### **Summary of Next Steps**

1. **Backend**: Complete the FastAPI upload endpoint and ensure it’s running.
2. **Frontend**: Set up React, create the drag-and-drop component, and test uploading files.
3. **Integration**: Enable communication between frontend and backend using CORS and Docker.

Would you like help getting started on any specific part of this plan, such as setting up FastAPI or creating the React project? Let me know if you have questions or need additional details!

