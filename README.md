# AI Career Advisor

A Django-based web application that helps users analyze their skills and find relevant job opportunities. The application provides skill analysis, job market matching, and real-time job listings from multiple sources.

## Features

- **Skill Analysis**: Enter your skills and get analyzed against various job market requirements
- **Job Market Matching**: See how well your skills match different job roles
- **Real-time Job Listings**: Get relevant job opportunities from multiple sources
- **Modern UI**: Clean and responsive interface built with Tailwind CSS
- **Interactive Experience**: Real-time feedback and loading states

## Tech Stack

- **Backend**: Django 5.2
- **Frontend**: 
  - HTML5
  - Tailwind CSS
  - JavaScript
- **APIs**:
  - Remotive API
  - Adzuna API
  - JSearch API

## Project Structure

```
AI-career-advisor/
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── templates/
├── jobs/
│   ├── views.py
│   ├── urls.py
│   ├── models.py
│   └── services.py
├── career_advisor/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ai-career-advisor.git
   cd ai-career-advisor
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Seed the database**:
   ```bash
   python manage.py seed_job_markets
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

7. **Access the application**:
   Open your browser and navigate to `http://127.0.0.1:8000/`

## Production Deployment

For deploying the application to production for all users, follow these steps:

1. **Set up environment variables**:
   Copy the `.env.example` file to `.env` and fill in all the required values:
   ```bash
   cp .env.example .env
   # Edit the .env file with your production values
   ```

2. **Database setup**:
   The application is configured to use PostgreSQL in production. Make sure to:
   - Create a PostgreSQL database
   - Update the database credentials in your `.env` file

3. **Using Docker (recommended)**:
   ```bash
   # Build and run using docker-compose
   docker-compose up -d
   
   # Run migrations
   docker-compose exec web python manage.py migrate
   
   # Create a superuser
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Manual deployment**:
   If not using Docker:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Collect static files
   python manage.py collectstatic
   
   # Run migrations
   python manage.py migrate
   
   # Start the server with gunicorn
   gunicorn career_advisor.wsgi:application
   ```

5. **Set up a reverse proxy**:
   For production, use Nginx or Apache as a reverse proxy in front of Gunicorn.

6. **SSL Certificate**:
   Secure your application with an SSL certificate using Let's Encrypt.

## Usage

1. Enter your skills in the textarea (one skill per line)
2. Click "Analyze Skills"
3. View your skill analysis and matching job opportunities
4. Explore job listings from various sources

## API Keys

The application uses several APIs that require API keys:

1. **Adzuna API**:
   - Get your API keys from [Adzuna](https://developer.adzuna.com/)
   - Add them to your environment variables:
     ```
     ADZUNA_APP_ID=your_app_id
     ADZUNA_APP_KEY=your_app_key
     ```

2. **JSearch API**:
   - Get your API key from [RapidAPI](https://rapidapi.com/letscrape-6bRBaEHQd/api/jsearch)
   - Add it to your environment variables:
     ```
     JSEARCH_API_KEY=your_api_key
     ```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Django](https://www.djangoproject.com/) - The web framework used
- [Tailwind CSS](https://tailwindcss.com/) - The CSS framework used
- [Remotive](https://remotive.com/) - Job listings API
- [Adzuna](https://www.adzuna.com/) - Job search API
- [JSearch](https://jsearch.com/) - Job search API

Deployed Link : https://career-compass-dyqc.onrender.com/
