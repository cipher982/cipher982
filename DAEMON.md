# Profile Updater Daemon

## ✅ Status: Running

Your profile dashboard now updates automatically **every 2 hours** via macOS LaunchAgent.

## 🎮 Management Commands

```bash
# Check status
./scripts/manage_daemon.sh status

# View live logs
./scripts/manage_daemon.sh logs

# Run update immediately (don't wait for timer)
./scripts/manage_daemon.sh run-now

# Restart daemon (if you change scripts)
./scripts/manage_daemon.sh restart

# Stop daemon
./scripts/manage_daemon.sh stop

# Start daemon
./scripts/manage_daemon.sh start

# View errors
./scripts/manage_daemon.sh errors
```

## 📁 File Locations

```
~/Library/LaunchAgents/com.cipher982.profile-updater.plist  # LaunchAgent config
~/logs/cipher982.log                                         # Standard output
~/logs/cipher982.error.log                                   # Errors only
```

## 🔧 How It Works

**LaunchAgent runs every 2 hours:**
1. Collects data (git, Claude, Codex sessions)
2. Generates hero.svg
3. Updates README.md
4. Commits & pushes to GitHub (if changes detected)

**Benefits:**
- ✅ Survives laptop sleep/wake
- ✅ Auto-starts on login
- ✅ Explicit logs (no cron mystery)
- ✅ macOS native (launchd is built-in)

## 🐛 Troubleshooting

**Daemon not running?**
```bash
./scripts/manage_daemon.sh start
```

**Check for errors:**
```bash
./scripts/manage_daemon.sh errors
```

**View what's happening:**
```bash
./scripts/manage_daemon.sh logs
```

**Git push failing?**
- Check GitHub auth: `git push` manually from `~/git/cipher982`
- Check SSH keys: `ssh -T git@github.com`

**Python path issues?**
```bash
# Find your python3 location
which python3

# Update PLIST if needed
vim ~/Library/LaunchAgents/com.cipher982.profile-updater.plist
# Change: /usr/local/bin/python3 to your actual path
```

## 🎨 GUI Option: LaunchControl

**Want a visual interface?**

Install [LaunchControl](https://www.soma-zone.com/LaunchControl/) ($15):
- See all LaunchAgents in one place
- Start/stop with buttons
- View logs in UI
- Get notifications on failures

Your agent will show up as `com.cipher982.profile-updater`.

## 📊 Expected Behavior

**Timeline:**
- **Every 2 hours:** Daemon wakes up
- **~10 seconds:** Collects data, generates assets
- **If changes detected:** Commits and pushes to GitHub
- **If no changes:** Exits silently

**GitHub profile updates:**
- Usually within 1-2 minutes of push
- May cache up to 5 minutes

**When laptop is closed:**
- Daemon doesn't run (no power)
- Resumes on next wake
- This is fine! If laptop closed, you're not coding → no new data

## 🔄 Making Changes

**If you modify scripts:**
```bash
# Daemon picks up changes automatically (no restart needed)
# But if you want immediate update:
./scripts/manage_daemon.sh run-now
```

**If you change update frequency:**
```bash
# Edit the plist
vim ~/Library/LaunchAgents/com.cipher982.profile-updater.plist

# Change this line:
# <integer>7200</integer>  <!-- 2 hours in seconds -->

# To (for example, 1 hour):
# <integer>3600</integer>

# Restart daemon
./scripts/manage_daemon.sh restart
```

## 🚀 Next Run

Check when it last ran:
```bash
stat -f "%Sm" ~/logs/cipher982.log
```

Next run will be ~2 hours after that timestamp.

---

**Everything is set up and running! Your GitHub profile will auto-update every 2 hours. 🎉**
