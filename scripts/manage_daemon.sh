#!/bin/bash
# Helper script to manage the profile updater daemon

PLIST=~/Library/LaunchAgents/com.cipher982.profile-updater.plist
LOG=~/logs/cipher982.log
ERROR_LOG=~/logs/cipher982.error.log

case "$1" in
  start)
    echo "🚀 Starting profile updater daemon..."
    launchctl load "$PLIST"
    echo "✅ Daemon started (runs every 2 hours)"
    ;;

  stop)
    echo "🛑 Stopping profile updater daemon..."
    launchctl unload "$PLIST"
    echo "✅ Daemon stopped"
    ;;

  restart)
    echo "🔄 Restarting profile updater daemon..."
    launchctl unload "$PLIST" 2>/dev/null
    launchctl load "$PLIST"
    echo "✅ Daemon restarted"
    ;;

  status)
    echo "📊 Daemon status:"
    if launchctl list | grep -q cipher982; then
      launchctl list | grep cipher982
      echo ""
      echo "✅ Running"
      echo ""
      echo "📋 Last 10 log entries:"
      tail -10 "$LOG" 2>/dev/null || echo "No logs yet"
    else
      echo "❌ Not running"
    fi
    ;;

  logs)
    echo "📋 Tailing logs (Ctrl-C to exit)..."
    tail -f "$LOG"
    ;;

  errors)
    echo "⚠️  Error log:"
    cat "$ERROR_LOG" 2>/dev/null || echo "No errors logged"
    ;;

  run-now)
    echo "▶️  Running update immediately..."
    cd ~/git/cipher982 && ./scripts/update_local.sh
    ;;

  *)
    echo "Usage: $0 {start|stop|restart|status|logs|errors|run-now}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the daemon"
    echo "  stop     - Stop the daemon"
    echo "  restart  - Restart the daemon"
    echo "  status   - Check if daemon is running"
    echo "  logs     - View live logs"
    echo "  errors   - View error log"
    echo "  run-now  - Trigger an immediate update"
    exit 1
    ;;
esac
