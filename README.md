## 📝 Complaint Box – Mini Full Stack Project

A simple "Full-stack web application" where users can register, log in, submit complaints, and an admin can view all complaints.
This project is built for learning full-stack development using React, Flask and MySQL.


## 🚀 Features
### 👤 User
1. Attractive homepage with animated background
2. User registration & login
3. Add complaints after login
4. Can view their complaints.
5. Logout & navigation (Back to Home / Dashboard)
      

### 🔐 Admin
1. Separate admin login
2. View all complaints submitted by users
3. Can view, delete and show resolve status of the complaits
4. Logout & back to home option


## 🛠️ Tech Stack

1. Frontend: React + Vite
2. Backend: Python (Flask)
3. Database: MySQL
4. Environment Variables: python-dotenv



## 🔐 Environment Variables (.env)

#### Create a .env file in the root folder:  (⚠️ .env file is ignored using .gitignore for security.)
and put the following code-

       DB_HOST=localhost
       DB_USER=root
       DB_PASSWORD=your_mysql_password
     DB_NAME=complaint_box
     SECRET_KEY=replace_with_a_long_random_secret

Use `.env.example` as the template, then save your actual values in `.env`.



## 🗄️ Database Setup (MySQL)

#### Run the following SQL queries in MySQL Workbench:
              
              CREATE DATABASE complaint_box;
              USE complaint_box;
              
              CREATE TABLE users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
               );
              
              CREATE TABLE complaints (
               id INT AUTO_INCREMENT PRIMARY KEY,
               user_id INT NOT NULL,
               title VARCHAR(255) NOT NULL,
               category VARCHAR(100) NOT NULL,
               description TEXT NOT NULL,
               status VARCHAR(20) DEFAULT 'pending',
               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
               FOREIGN KEY (user_id) REFERENCES users(id)
              );
              
             CREATE TABLE admin (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  username VARCHAR(100) NOT NULL UNIQUE,
                  password VARCHAR(255) NOT NULL
               );
              



## 📦 Installation & Setup
#### 1️⃣ Create virtual environment
python -m venv venv
#### 2️⃣ Activate virtual environment
venv\Scripts\activate
#### 3️⃣ Install dependencies
pip install -r requirements.txt
#### ▶️ Run the Project
#### Start the Flask API (from the project root)
python app.py

#### Start the React frontend (in a second terminal)
cd frontend
npm install
npm run dev

Open the frontend URL shown by Vite, usually `http://localhost:5173`.



## 📌 Notes

1. Passwords are stored using Werkzeug hashing.
2. This project is suitable for:
     College mini-project
     Full-stack practice
     GitHub portfolio



## 🌟 Future Improvements

1. Email notifications for status changes
2. File attachments on complaints
3. Production deployment configuration



## 👩‍💻 Author

Shruti Kumari

BTech cse (Data Science)

Mini fullStack project using Flask and MySQL.




