# Email list: Free MTD Ready Kit

Nothing here has been sent or signed up for. These are drafts and setup notes for D.

## The hook (lead magnet)
**Free MTD Ready Kit: every deadline for 2026 to 2028, a getting-ready checklist, and an email reminder 7 days before every HMRC deadline.**

Options considered:
1. **MTD Ready Kit (chosen).** Deadline calendar PDF + .ics calendar file + checklist + reminder emails. It solves a recurring, real fear (4 updates a year, £200 penalty after 4 points from 2027-28), keeps subscribers opening emails all year (good deliverability and repeat traffic to the directory), and works for landlords, sole traders and accountants alike. All facts come from GOV.UK, so it's accurate and cheap to maintain.
2. "Which MTD software fits me?" personalised shortlist. Strong buying intent, but it needs a quiz and leans on affiliate picks, which weakens trust in a new site.
3. "Am I ready for MTD?" self-assessment score. Engaging, but one-off, so less reason to stay subscribed.

Asset files (rebuild with `python3 scripts/make_kit.py` after changing the site name or dates):
- `kit/mtd-ready-kit-2026-28.pdf` (5 pages, A4) · source `kit/kit.html` · data `data/deadlines.json` (every date with its GOV.UK source)
- `kit/mtd-deadlines-2026-28.ics` (13 future dates, each with a 7-day alert)
- Published at `/kit/…` (blocked in robots.txt; linked from `/free-mtd-kit/` as a direct download until email sign-up is configured, and from the welcome email and `/free-mtd-kit/confirmed/` once it is).

## Recommended provider: Brevo (free plan)
Checked on the providers' own sites, 18 November 2026:

| Provider | Free plan | Automations on free? | Paid from | Fit |
|---|---|---|---|---|
| **Brevo** | 300 emails/day, up to 100,000 contacts stored, double opt-in forms with embeddable HTML, API, EU servers | **Yes**, up to 2,000 contacts entering automations | Starter $9/month ($97/year) removes the daily limit; Standard $18/month for unlimited automations | **Best fit**: welcome sequence + reminders work for free, list size isn't capped, list stats via API |
| MailerLite | 250 subscribers, 2,500 emails/month | Yes, but 3 active automations, max 5 steps | Comfort from $12/month | Good tool, but 250-subscriber cap arrives fast |
| Kit (ConvertKit) | Up to 10,000 subscribers, unlimited forms and broadcasts, API | **No**: sequences and visual automations need Creator | Creator (paid) | Can't send the welcome sequence on free |
| Buttondown | First 100 subscribers | Automations are a +$29/month add-on | Usage-based + add-ons | Too small on free |

Sources: https://www.brevo.com/pricing/ · https://help.brevo.com/hc/en-us/articles/208580669-FAQs-What-are-the-limits-of-the-Free-plan · https://help.brevo.com/hc/en-us/articles/208589409-About-Brevo-s-pricing-plans · https://help.brevo.com/hc/en-us/articles/360001005510-Data-storage-location · https://www.mailerlite.com/pricing · https://help.kit.com/en/articles/16627071-the-kit-free-plan · https://buttondown.com/pricing

Brevo caveats: free emails carry a "Sent with Brevo" footer; campaigns over 300 recipients need re-queuing across days, so move to Starter once the list nears ~250 (reminders should land on the same day). Brevo prices are shown in USD on its site; confirm the GBP amount at checkout.

## What D needs to do (about 30–40 minutes)
1. **Create a free Brevo account** at brevo.com: your name, email, organisation name (site name), website URL and a postal/contact address (required in email footers). Brevo approves new accounts for sending.
2. **Authenticate the domain** once it's registered (Brevo > Senders, domains: add the DNS records it gives you at Fasthosts) and set the sender to something like `hello@<domain>`.
3. **Contacts > Settings > Contact attributes:** check `FIRSTNAME` exists; add a **Text** attribute `MTD_ROLE`.
4. **Contacts > Lists:** create "MTD Ready Kit". Note its ID → `config/email.json` `list_id`.
5. **Marketing > Forms > Create sign-up form (Full page/embedded):** fields Email, FIRSTNAME, MTD_ROLE (optional text field). Leave "Enable Opt-in field" OFF (see consent note) and CAPTCHA OFF (our form handles spam with a honeypot). Settings: **Double confirmation email** using the template in `00-double-opt-in-confirmation.md`; "Confirmation page after submitting" = `<site>/free-mtd-kit/check-your-inbox/`; "Confirmation page after clicking the validation link" = `<site>/free-mtd-kit/confirmed/`; final confirmation email = `01-welcome-kit-delivery.md` (or send it as automation step 1). List = "MTD Ready Kit".
6. **Share > HTML:** copy the form's `action="https://….sibforms.com/serve/…"` URL into `config/email.json` `form_action`, set `"provider": "brevo"`, and check the field names match. Rebuild. I'll then submit a real test sign-up end to end before launch.
7. **Automations:** "Contact added to list" → (welcome, if not sent as final confirmation) → wait 2 days → `02` → wait 3 days → `03` → wait 5 days → `04`.
8. **Reminders:** schedule campaigns from `05-deadline-reminder-template.md`.
9. **Stats:** Brevo > SMTP & API > API keys → create a key and run `BREVO_API_KEY=… python3 scripts/stats.py`. Never commit the key.

## Consent: why there's no tick box
The form's only purpose is joining this email list, and the text right next to the button says exactly what people will get (kit, deadline reminders, occasional tips that may mention commission-earning software, one-click unsubscribe). Submitting it is a clear affirmative act, and the double opt-in click confirms it and gives Brevo a timestamped record. A separate tick box would ask for the same thing twice and lower sign-ups without adding protection. If we ever want to email about anything else (for example partner offers or accountant introductions), that needs its own separate, unticked opt-in. ICO references: https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/electronic-and-telephone-marketing/electronic-mail-marketing/ (PECR reg. 22: specific consent needed for marketing email to individuals and sole traders) and the ICO's consent guidance. Note the ICO says this guidance is under review after the Data (Use and Access) Act 2025.

The optional "I am a…" field is there for segmentation (landlord vs sole-trader reminders) and to spot accountants. It is optional and explained, in line with data minimisation.

## Files
- `00-double-opt-in-confirmation.md`: Brevo DOI email
- `01-welcome-kit-delivery.md`: welcome + kit links (immediate)
- `02-sequence-day2-five-decisions.md`, `03-sequence-day5-choosing-software.md` (affiliate disclosure inline), `04-sequence-day10-diy-or-accountant.md`
- `05-deadline-reminder-template.md`: reminder template + full send schedule to May 2028

Placeholders: `{{ contact.FIRSTNAME }}` and `{{ unsubscribe }}` are Brevo syntax; `https://mtdsoftwarecompare.co.uk` and `[Postal address to be added]` still need filling in. Sign-offs use Daniel Wyatt. The welcome email names 7 February 2027 as the next deadline: update it after that date.
