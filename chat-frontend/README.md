# OTRADE Bot - Chat Frontend

A modern, beautiful chat interface for testing the OTRADE wholesale trading bot.

## 🚀 Quick Deploy to Vercel

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Navigate to this directory**:
   ```bash
   cd chat-frontend
   ```

3. **Deploy**:
   ```bash
   vercel --prod
   ```

4. **Follow the prompts**:
   - Set up and deploy: `Yes`
   - Which scope: Choose your account
   - Link to existing project: `No`
   - Project name: `otrade-chat` (or your preferred name)
   - Directory: `./` (current directory)
   - Override settings: `No`

5. **Done!** Vercel will provide you with a live URL like:
   ```
   https://otrade-chat.vercel.app
   ```

## 📱 Features

- **Modern Design**: Premium glassmorphism UI with smooth animations
- **Real-time Chat**: Instant communication with the OTRADE bot
- **Session Management**: Persistent chat sessions with local storage
- **Mobile Responsive**: Works perfectly on all devices
- **Typing Indicators**: Visual feedback when bot is responding
- **Quick Suggestions**: Pre-configured prompts to get started

## 🧪 Local Testing

Simply open `index.html` in your web browser:

```bash
# Windows
start index.html

# macOS
open index.html

# Linux
xdg-open index.html
```

Or use a local server:

```bash
# Python 3
python -m http.server 8080

# Node.js (with http-server)
npx http-server -p 8080
```

Then visit: `http://localhost:8080`

## ⚙️ Configuration

The bot API endpoint is configured in `script.js`:

```javascript
const API_BASE_URL = 'https://otrade-bot.onrender.com';
```

To change the backend URL, edit this line in `script.js`.

## 📂 Files Structure

```
chat-frontend/
├── index.html      # Main HTML structure
├── style.css       # Premium styling and animations
├── script.js       # API integration and logic
├── vercel.json     # Vercel deployment config
└── README.md       # This file
```

## 🎨 Design Features

- **Gradient Backgrounds**: Vibrant purple-to-blue gradient theme
- **Glassmorphism**: Frosted glass effect for modern aesthetics
- **Smooth Animations**: Micro-interactions for enhanced UX
- **Custom Scrollbar**: Styled scrollbar matching the theme
- **Auto-resize Input**: Textarea expands as you type

## 🔧 Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Android)

## 💡 Tips for Client Testing

1. Share the deployed Vercel URL with your client
2. Bot is deployed at: `https://otrade-bot.onrender.com`
3. Sessions are saved in browser local storage
4. Click "New Chat" button to start fresh conversation
5. Use suggestion buttons for quick testing

## 🐛 Troubleshooting

**Bot not responding?**
- Check if backend at `https://otrade-bot.onrender.com/health` is online
- Render free tier may sleep after inactivity (first request takes ~30 seconds)
- Check browser console for errors (F12)

**Session not saving?**
- Ensure browser allows local storage
- Clear browser cache and try again

**Deployment failed?**
- Make sure you're in the `chat-frontend` directory
- Check Vercel CLI is installed: `vercel --version`
- Try: `vercel login` to re-authenticate

## 📞 Support

For issues or questions, contact the development team.

---

**Built with ❤️ for OTRADE**
