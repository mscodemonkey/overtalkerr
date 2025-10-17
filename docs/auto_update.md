# Auto-Update Feature

Overtalkerr includes a built-in auto-update feature that makes it easy to keep your installation up to date without SSH access.

## How It Works

1. **Automatic Update Checks**: The dashboard automatically checks GitHub for new releases
2. **One-Click Install**: When an update is available, click "Install Update" to run `git pull`
3. **Manual Restart**: After the update, restart the service to apply changes

## Using Auto-Update

### From the Dashboard

1. Open the Overtalkerr dashboard (http://your-server:5000)
2. If an update is available, you'll see a notification banner at the top
3. Click **"Install Update"** to download the latest version
4. After the update completes, restart the service:

   ```bash
   systemctl restart overtalkerr
   ```

5. Refresh the dashboard to see the new version

### Manual Update via CLI

If you prefer the traditional method:

```bash
cd /opt/overtalkerr
git pull
systemctl restart overtalkerr
```

## Update Process

The auto-update feature:

1. ✅ Checks if you're in a git repository
2. ✅ Runs `git pull` to download the latest code
3. ✅ Reports success/failure
4. ✅ Tells you if a service restart is needed

## Important Notes

- **Service Restart Required**: Updates don't take effect until you restart the service
- **Git Repository Required**: Auto-update only works if Overtalkerr was installed via git
- **No Automatic Restart**: For safety, you must manually restart the service
- **Configuration Preserved**: Your `.env` configuration is never overwritten by updates

## Troubleshooting

### "Not a git repository"

If you see this error, you installed Overtalkerr without git. To enable auto-update:

```bash
cd /opt
mv overtalkerr overtalkerr.backup
git clone https://github.com/mscodemonkey/overtalkerr.git
cp overtalkerr.backup/.env overtalkerr/.env
systemctl restart overtalkerr
```

### "Git pull failed"

This usually means you have local changes that conflict with the update. To resolve:

```bash
cd /opt/overtalkerr
git stash  # Save your local changes
git pull   # Get the update
git stash pop  # Restore your changes
```

### Update Button Doesn't Work

1. Check that the Overtalkerr user has git installed
2. Verify the repository is clean: `git status`
3. Check logs: `journalctl -u overtalkerr -n 50`

## Security Considerations

- The `/api/update` endpoint requires no authentication (assumes local network)
- Updates come directly from GitHub
- No automatic restarts means you control when changes take effect
- Your configuration and database are never modified by updates

## What Gets Updated

When you run an update:

- ✅ Application code (`*.py`, `*.html`, `*.js`)
- ✅ Documentation (`*.md`)
- ✅ Configuration templates
- ❌ Your `.env` file (preserved)
- ❌ Your database (preserved)
- ❌ System service configuration (preserved)

## Rollback

If an update causes issues, you can rollback:

```bash
cd /opt/overtalkerr
git log --oneline  # See recent commits
git reset --hard <commit-hash>  # Go back to a working version
systemctl restart overtalkerr
```

Replace `<commit-hash>` with the commit you want to return to.
