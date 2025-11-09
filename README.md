# Ping Pong Tracker

A web application for tracking ping pong games, ELO ratings, and tournaments.

## Features

- 🏓 **ELO Rating System** - Track singles and doubles ratings
- 📱 **Phone Authentication** - Secure user registration with SMS verification
- 🎮 **Game Reporting** - Report games with verification from opponent
- 🏆 **Tournaments** - Create and manage bracket-style tournaments
- 📊 **Rankings** - View ELO rankings and weekly leaderboards
- 🏅 **Trophies & Achievements** - Earn rewards for milestones
- 💬 **Game Comments** - Discuss games with other players

## Tech Stack

- **Backend**: Django + Django REST Framework
- **Frontend**: Vue 3 + Vite + Vuetify 3
- **Database**: SQLite (development)
- **Authentication**: Phone number + SMS verification

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Development Workflow

### Registration Process
1. User registers with phone number
2. Verification code is sent (prints to console in dev mode)
3. User verifies phone number
4. Admin approves account via Django admin
5. User can now access all features

### Admin Panel
Access the Django admin at `http://localhost:8000/admin` to:
- Approve new user registrations
- Manage games and resolve disputes
- View all data and statistics

### Environment Variables

Create `.env` files in both backend and frontend directories:

**backend/.env**
```env
# Django settings
SECRET_KEY=your-secret-key-here
DEBUG=True

# Twilio settings (optional for development)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Admin settings
ADMIN_EMAIL=admin@example.com
```

**frontend/.env**
```env
VITE_API_URL=http://localhost:8000/api
```

## API Endpoints

- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/verify-phone/` - Verify phone number
- `GET /api/rankings/` - Get rankings and leaderboards
- `GET/POST /api/games/` - Game management
- `GET/POST /api/tournaments/` - Tournament management
- `GET /api/profiles/` - User profiles

## Features Status

✅ **Completed:**
- User registration with phone verification
- Login/logout functionality
- ELO calculation system
- Django models and API
- Basic Vue.js frontend structure

🚧 **In Progress:**
- Game reporting form
- Game verification workflow
- User profile pages

📋 **Planned:**
- Tournament bracket generation
- Weekly trophy system
- Game chat/comments
- Advanced statistics

## Notes

- Phone verification codes print to Django console in development mode
- Admin approval is required for new accounts
- ELO system uses standard K-factor adjustments
- Doubles games use 75% of normal K-factor per player