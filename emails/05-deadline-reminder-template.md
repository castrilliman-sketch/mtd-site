# Deadline reminder template (send 7 days before each deadline)

Send as a scheduled Brevo **campaign** to the MTD Ready Kit list (not an automation), one per deadline. Fill in the [BRACKETS] from the
schedule below. Every date is from data/deadlines.json (sources: GOV.UK, checked 18 November 2026). Re-check GOV.UK before each send.

**Subject:** 7 days to go: MTD [UPDATE_NAME] due [WEEKDAY DATE]
**Preview text:** [ONE_LINE_WHO]. Here's a 10-minute checklist.

---

Hi {{ contact.FIRSTNAME }},

A quick reminder: **[UPDATE_NAME] is due on [WEEKDAY DATE]**.
[WEEKEND_LINE e.g. "That's a Sunday, so aim to send it by Friday 5 February."]

**Who this is for:** [WHO, e.g. "anyone already using Making Tax Digital for Income Tax (you started in April 2026)." ]
[IF NOT YET IN MTD: "If you start in April 2027 or later, you can ignore this one. We'll remind you when yours are due."]

**Your 10-minute checklist**
1. Bring your records up to date to [PERIOD_END].
2. Check the totals your software shows. Each update covers the tax year so far, so earlier corrections flow through.
3. Send an update for each business, even if nothing happened in the period.
4. Check your HMRC online account says "You sent a quarterly update".
5. Look at the tax estimate and put money aside.

[PENALTY_LINE: for 2026 to 2027 updates: "HMRC won't give penalty points for late quarterly updates in 2026 to 2027, but you must send them before you can submit your tax return." / from 2027 to 2028: "Each late update now earns a penalty point, and 4 points means a £200 penalty."]

Next deadline after this one: [NEXT_DEADLINE].

[D's first name], PlainMTD

Source: [Send quarterly updates](https://www.gov.uk/guidance/use-making-tax-digital-for-income-tax/send-quarterly-updates) (GOV.UK) · *General information, not tax advice.*
[Operator contact] · {{ unsubscribe }}

---

## Schedule (send dates are 7 days before; UK time, 8am)

| Send on | Deadline | What | Who | Penalty line |
|---|---|---|---|---|
| Sun 24 Jan 2027 | Sun 31 Jan 2027 | 2025 to 2026 Self Assessment return and payment | Everyone in Self Assessment (normal online return) | Normal SA late-filing penalties |
| Sun 31 Jan 2027 | Sun 7 Feb 2027 | Quarterly update 3, 2026 to 2027 (to 5 January) | Already in MTD since April 2026 | No points in 2026-27 |
| Mon 1 Mar 2027 | Tue 6 Apr 2027 | Heads-up: MTD starts for qualifying income over £30,000 (send ~5 weeks ahead, not 7 days) | April 2027 joiners | n/a |
| Fri 30 Apr 2027 | Fri 7 May 2027 | Quarterly update 4, 2026 to 2027 (to 5 April) | Already in MTD since April 2026 | No points in 2026-27 |
| Sat 31 Jul 2027 | Sat 7 Aug 2027 | Quarterly update 1, 2027 to 2028 (to 5 July) | Everyone in MTD, incl. April 2027 joiners' first update | 4 points = £200 |
| Sun 31 Oct 2027 | Sun 7 Nov 2027 | Quarterly update 2, 2027 to 2028 (to 5 October) | Everyone in MTD | 4 points = £200 |
| Mon 24 Jan 2028 | Mon 31 Jan 2028 | 2026 to 2027 tax return (through MTD software if you started April 2026) | Everyone in Self Assessment | Late returns get points |
| Mon 31 Jan 2028 | Mon 7 Feb 2028 | Quarterly update 3, 2027 to 2028 (to 5 January) | Everyone in MTD | 4 points = £200 |
| Sun 30 Apr 2028 | Sun 7 May 2028 | Quarterly update 4, 2027 to 2028 (to 5 April) | Everyone in MTD | 4 points = £200 |

Payments on account (31 July) can be added as a one-line note in the 31 July 2027 / 7 August 2027 email rather than a separate send.

**Brevo free-plan note:** the free plan sends up to 300 emails a day. Once the list passes about 250 people, move to the Starter plan
(from $9 a month) so each reminder reaches everyone on the same day.
