---
title: "I Built an AI Agent That Fixes Production Crashes & Opens PRs (So You Don't Have to Wake Up at 3 AM)"
description: "AutoFixer watches logs, detects crashes, generates fixes with Gemini AI, and automatically opens GitHub PRs. Here's the full story."
tags: ai, python, devops, github, automation
cover_image: https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=1200&h=630&fit=crop
canonical_url: https://github.com/turfin-logic/autofixer-agent
---

# I Built an AI Agent That Fixes Production Crashes & Opens PRs

It's 3:47 AM. Your production server just crashed.

Normally, this means:
- 🚨 Pager alarm wakes you up
- 😵 You SSH into the server, grep logs
- 🔧 Manually find & fix the bug (half-asleep, mistakes happen)
- ⏰ Wait 30+ minutes for CI/CD validation
- 😰 Can't sleep because you're paranoid about rollback

**I got tired of this.**

So I built **AutoFixer** — an autonomous AI agent that does all of this automatically. In 6 seconds.

---

## The Problem: Reactive DevOps is Exhausting

Every production incident follows the same painful workflow:

```
3 AM: CRASH
↓
3:05 AM: Pager alert (goodbye sleep)
↓
3:10 AM: SSH + grep logs
↓
3:20 AM: Find the bug, understand the context
↓
3:35 AM: Write fix (tired, prone to errors)
↓
3:40 AM: Commit + push
↓
4:10 AM: Wait for CI/CD
↓
4:15 AM: Test in staging
↓
4:45 AM: Finally roll out fix
↓
5:00 AM: Can't fall back asleep
↓
6:00 AM: Tired for entire day
```

**This is broken.** And it happens dozens of times per year.

---

## The Solution: Autonomous AI That Never Sleeps

What if production crashes looked like this instead?

```
3:47 AM: Production crash happens
↓
3:47:02 AM: AutoFixer detects error in logs
↓
3:47:04 AM: Gemini AI analyzes stack trace
↓
3:47:06 AM: AI generates code fix
↓
3:47:08 AM: AutoFixer opens GitHub PR
↓
6:00 AM: You wake up to a PR waiting for review
↓
6:05 AM: You review + merge in 2 minutes
↓
6:10 AM: Fix is deployed, zero sleep lost
```

**That's AutoFixer.**

---

## How It Works (3-Layer Architecture)

### **Layer 1: Log Watcher 👀**

AutoFixer runs as a background daemon that continuously monitors your error logs:

```python
# Example: error.log is being watched
Traceback (most recent call last):
  File "src/payment.py", line 142
    user = db.query(user_id)  # Returns None sometimes
    print(user['email'])       # KeyError!

Error detected:
- Type: KeyError
- File: src/payment.py
- Line: 142
```

---

### **Layer 2: AI Root Cause Analysis 🧠**

Using **Google Gemini API**, AutoFixer analyzes the stack trace + surrounding code:

```json
{
  "error": "KeyError: 'email'",
  "root_cause": "user object is None when database query fails",
  "fix_type": "Defensive check",
  "suggested_code": "user = db.query(user_id) or {}\nemail = user.get('email', 'noreply@example.com')",
  "confidence": 0.95,
  "reasoning": "Query can return None during connection issues. Should handle gracefully."
}
```

---

### **Layer 3: Autonomous PR Creation 🚀**

AutoFixer automatically:

```
1. Creates new branch: fix/keyerror-payment-line-142
2. Applies the fix to src/payment.py
3. Validates syntax & imports locally
4. Commits with descriptive message
5. Pushes to GitHub
6. Opens PR with analysis + fix code
7. Tags you as reviewer
```

---

## Tech Stack

**Simple & elegant:**

```
watchdog==3.0.0              # File system monitoring
google-generativeai==0.8.3   # Gemini API
PyGithub==2.1.1              # GitHub automation
python-dotenv==1.0.0         # Environment management
requests==2.31.0             # HTTP client
```

**Total setup time: 5 minutes**

---

## Installation

### 1. Clone
```bash
git clone https://github.com/turfin-logic/autofixer-agent.git
cd autofixer-agent
```

### 2. Install
```bash
pip install -r requirements.txt
```

### 3. Get API Keys
- **Gemini:** https://console.cloud.google.com (free tier available)
- **GitHub:** https://github.com/settings/tokens (permissions: `repo`, `workflow`)

### 4. Configure
```bash
cp .env.example .env
# Edit with your keys
```

### 5. Run
```bash
python main.py
```

---

## Live Demo

```bash
# Terminal 2: Simulate a crash
echo "Traceback (most recent call last):" >> error.log
echo "  File \"src/app.py\", line 42, in <module>" >> error.log
echo "    print(user['name'])" >> error.log
echo "KeyError: 'name'" >> error.log
```

Watch Terminal 1:

```
🚨 New crash detected!
📝 Error: KeyError: 'name'
📂 File: src/app.py:42
🔍 Analyzing with Gemini...
🧠 Fix confidence: 92%
✍️  Generating fix code...
🚀 Creating PR...
✅ PR opened: github.com/your-repo/pull/123
```

---

## Why This Matters

### For Developers:
✅ No more 3 AM wake-ups
✅ Fixes ready by morning
✅ Learn AI-suggested patterns
✅ Better sleep = better code

### For Teams:
✅ MTTR drops from 30 min to 6 sec
✅ Less human error
✅ Better work-life balance

### For Companies:
✅ Fewer P1 incidents
✅ Faster deployment
✅ Reduced on-call burnout

---

## Real Examples

**Before vs After**

```python
# ❌ CRASH: KeyError
result = api_response['user']
print(result['email'])

# ✅ AUTOFIXER FIX:
result = api_response.get('user', {})
print(result.get('email', 'unknown@example.com'))
```

---

## The Safety Layer

AutoFixer has guardrails:

```python
# 1. Syntax validation
ast.parse(generated_code)

# 2. Never touches main branch
# Only creates PRs, requires human review

# 3. Confidence thresholds
if confidence < 0.75:
    print("⚠️ Low confidence - requires manual review")
```

---

## Limitations

❌ Can't fix architectural issues (only code-level bugs)
❌ Needs complete stack traces
❌ Python-only (for now)

✅ Always requires human review
✅ Never auto-merges

---

## Get Started

```bash
git clone https://github.com/turfin-logic/autofixer-agent
cd autofixer-agent
pip install -r requirements.txt
python main.py
```

**GitHub:** https://github.com/turfin-logic/autofixer-agent

---

## Questions?

💬 Open an issue on GitHub
🐦 [@turfin_logic](https://twitter.com/turfin_logic)

---

If AutoFixer saves you from one production incident, that's one less sleepless night.

⭐ Drop a star on the repo if you find it useful.

#DevOps #AI #Python #Automation #OpenSource #GitHub
