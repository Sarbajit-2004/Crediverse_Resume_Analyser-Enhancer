Crediverse Resume Analyzer(V0)

[Python Badge] [Streamlit Badge] [MySQL Badge] [NLP Badge] [License Badge]


An AI-powered resume analysis tool that helps job seekers and students improve their resumes, get smart career recommendations, and receive personalized course and skill suggestions. Built with Streamlit, NLP, and MySQL, it also provides an Admin Dashboard for insights and reporting.


✨ Features
•	📄 Resume Parsing & Analysis – Extracts details like name, email, skills, education, and experience.

•	📝 Resume Scoring – Rates resumes based on sections like Objective, Projects, Achievements, etc.

•	🎯 Career Field Prediction – Detects whether the user belongs to Data Science, Web Dev, Android, iOS, or UI/UX.

•	💡 Skill & Course Recommendations – Suggests missing skills and curated courses.

•	🎓 Learning Support – Resume tips, interview prep videos, and career guidance.

•	📊 Admin Dashboard – View user data, download reports, and explore pie-chart visualizations.

•	🗄 Database Integration – Stores data in MySQL for structured insights.


🛠 Tech Stack
•	Frontend: Streamlit
•	Backend: Python
•	Database: MySQL
•	AI/NLP: PyResparser, SpaCy, NLTK
•	Visualization: Plotly, Pandas


⚙️ Installation

1. Clone the repository:
•	git clone [https://github.com/Sarbajit-2004/Crediverse_Resume_Analyzer-Enhancer.git](https://github.com/Sarbajit-2004/Crediverse_Resume_Analyser-Enhancer)
cd Crediverse-Resume-Analyzer

2. Create a virtual environment & activate it:
•	python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

3. Install dependencies:
•	pip install -r requirements.txt

4. Install NLP models:
•	python -m nltk.downloader stopwords
python -m spacy download en_core_web_sm

5. Set up MySQL database:
•	- Create a database named cv.
- Update your DB credentials in App.py.
- The app will auto-create the user_data table if it doesn’t exist.


▶️ Usage
Run the Streamlit app:
•	streamlit run App.py

- User Mode – Upload resumes and get analysis + recommendations.
 
- Admin Mode – Secure login to view analytics, download data, and visualize trends


📸 Screenshots

🔹 Home Page – <img width="1919" height="1079" alt="image" src="https://github.com/user-attachments/assets/abf18d40-91e8-485e-89ca-78438c524023" />

🔹 Resume Upload & Analysis - <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/56306c18-f818-407d-ad9e-aa4711fbd8e2" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/05512141-e03f-4d0f-949d-cd826e43085e" />

  
 
🔹 Admin Dashboard –  <img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f59672de-8e63-47e7-925c-bc927d6db0d4" />
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/dce75cd6-7de8-41f8-9a6b-acb81198b035" />



 

📈 Future Enhancements
•	✅ AI-based grammar & language improvements.

•	✅ Resume vs Job Description matching.

•	✅ Multi-resume comparison for recruiters.

•	✅ Blockchain-verified certifications integration.


👨‍💻 Author

Developed with ❤️ by Sarbajit Kumar De
