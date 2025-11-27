# ⚠️ DEPRECATED: Google Assistant / Dialogflow Integration

**This guide is no longer applicable.**

Google deprecated **Conversational Actions** in **June 2023**, which means you can no longer create custom voice apps for Google Assistant using Dialogflow.

## What Happened?

Google shut down support for third-party conversational apps (like Overtalkerr) and now only supports:
- **App Actions** - For Android apps published on Google Play Store
- **Google Home Platform** - For smart home devices

Web services like Overtalkerr **cannot** integrate directly with Google Assistant anymore.

## Alternative: Use Home Assistant

If you want to use "Hey Google" with Overtalkerr, use the **Home Assistant Assist integration** instead:

### How It Works

1. Home Assistant has official Google Assistant support (they're big enough that Google still supports them)
2. You connect Overtalkerr to Home Assistant via webhook-conversation
3. Say "Hey Google, tell Home Assistant to download Inception"
4. Home Assistant → Overtalkerr → Your media backend

### Setup Guide

Follow the complete setup guide here: **[How to Setup Home Assistant](how_to_setup_home_assistant.md)**

This is the **only supported way** to use "Hey Google" with Overtalkerr.

## Why Dialogflow Code Was Removed

As of this update, the Google Assistant adapter has been removed from Overtalkerr because:
- It cannot be used with Google Assistant
- It created confusion for users
- Maintaining dead code wastes development time

The `/voice` endpoint still exists and works with Siri Shortcuts and other webhook-based integrations.

---

**For "Hey Google" voice control:** Use [Home Assistant Assist](how_to_setup_home_assistant.md)

**For other voice assistants:** Use [Alexa](how_to_setup_alexa.md) or [Siri](how_to_setup_siri.md)
