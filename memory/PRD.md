# Know Your Rights - PRD

## App Summary
A teen-friendly mobile app that helps users understand basic rights in stressful real-life situations. Educational only, not legal advice.

## Target Users
Teens and young adults

## Core Features (Completed)
1. **Home Screen** - Category grid (School, Work, Housing, Police, Online, Public Spaces, Immigration, Customer Service)
2. **Situation-based Guidance** - 292 pre-loaded scenarios with short answers, explanations, scripts, and next steps
3. **Emergency Mode** - Scripts, quick notify emergency contact, notes, timer
4. **AI Helper (Claude)** - Answers rights-related questions in simple language
5. **Scripts Section** - 292 copyable scripts organized by category with search
6. **Resource Section** - Hotlines, legal aid, and support contacts
7. **Legal Quotes** - "What the Law Says" section with Supreme Court/Constitution references for every scenario
8. **AI Scenario Generation** - If search yields no results, AI generates and saves new scenarios to MongoDB
9. **Settings** - Location detection, emergency contact setup, data management

## Design Theme
- **White, minimalistic** vibe throughout the entire app
- Background: `#FAFAFE`
- Cards: `#FFFFFF` with `#F1F1F5` borders
- Primary text: `#1E1B4B`
- Secondary text: `#64748B`
- Accent: `#8B5CF6` (purple)
- Emergency accent: `#EF4444` (red)

## Tech Stack
- Frontend: Expo (React Native), Expo Router
- Backend: FastAPI (Python), Uvicorn
- Database: MongoDB
- AI: Anthropic Claude via Emergent Integrations

## Navigation
- Tab-based: Home, Ask AI, Scripts, Resources, Settings
- Stack navigation for: Categories → Subcategories → Scenarios
- Full-screen modal: Emergency Mode
