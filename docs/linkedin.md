# LinkedIn pack

## Post

Guaranteed £5, or a 1 in 1,000 shot at £5,000?

I assumed people take the fiver when money's tight. 8 years of search data says it depends on how it gets tight.

I work in prize promotions, so I wanted to test it properly. I looked at Google searches in the UK and the UAE from 2019 to 2026: 32 search terms, 94 months, and 669 real search queries. The same 2026 war hit the UAE directly and the UK through fuel and energy prices, so comparing the two shows whether the route of a shock changes how people react.

What I found

→ UK, 2019 to 2025: prize searches grew 57% on average, guaranteed-reward searches 15%. "Giveaway" up 93%, "instant win" up 76%, cashback down 9%. A slow squeeze didn't put people off prizes.

→ UK, March 2026: when the Iran war sent fuel and energy prices up, cashback searches hit twice their winter level within a month and stayed high through September.

→ UAE, hit directly: cashback searches climbed until August instead of jumping in a month. "Offers" searches turned to food shopping too: 31% of them in 2025, 44% in 2026. Same shock, different speed.

How I built it

Collecting
→ Pulled each search term on its own. Put "prize draw" in the same request as "discount code" and Google rounds it to zero.

Classifying
→ Claude read all 669 queries and labelled each one: prize, saving, free gift, loyalty or nothing. Keyword rules can't tell a BMW M4 Competition from a radio competition.
→ Trained a simple model on those labels. It agreed with Claude 91% of the time. Keyword rules managed 73%.

Testing
→ Ramadan 2026 started ten days before the war, so the model controls for Ramadan.
→ Left "voucher code" out of the comparison. People switched to saying "discount code", so its drop is a change in wording, not in what they wanted.
→ Compared the same months every year. From March to September 2026, cashback searches were almost three times any year since 2019, including the 2022 cost-of-living spring.
→ Banks pushed cashback cards hard in 2026. Take cashback out and the UK effect shrinks by a third, but it's still there.

What I'd take into a promotions brief: a slow squeeze and a sudden shock push people in different directions. Prize mechanics held up through COVID and the cost-of-living crisis. Guaranteed rewards surged when a real shock landed.

One caveat: these are searches, not sales. They show what people wanted, not what they bought.

AI sped up the code. The questions, the checks and the calls on what the data can and can't say were mine.

Which would you take, the £5 or the shot at £5,000?

Code, data and method in the first comment.

#ConsumerBehaviour #Marketing #DataAnalytics #Promotions #AI

---

## Posting plan

- Post Tuesday to Thursday, 8 to 9am UK time. Upload the video natively (don't link to YouTube).
- Use the first frame as the thumbnail: it already shows the question.
- Put the GitHub link in the first comment and pin it. Links in the post body get shown to fewer people.
- Create the GitHub repo before posting, or the link in the video and comment will 404.
- Stay around for the first hour and reply to every comment with a question back. Don't edit the post in that hour.
- Repost to your own feed 1 to 2 days later with one line about the most interesting comment.

## Replies to have ready

**"Searches aren't sales."**
Agreed, and it's in the post. Search shows intent, and it reacts within the month, which is why it catches a shock that sales data would take a quarter to show. Next step would be pairing it with redemption data.

**"Correlation, not causation."**
Fair. Two countries is a case study, not proof. What I could do was try hard to break it. I pretended the shock happened in other months instead, 45 of them between 2021 and 2024, and none produced a jump anywhere near as big. I also rebuilt the index seven other ways (leaving out cashback, the vaguer "win" terms, voucher codes and so on) and controlled for Ramadan. The 2026 UK jump held every time. The UAE result is weaker, and the README says so.

**"Isn't the cashback spike just banks advertising cashback cards?"**
Partly, yes. The related searches are full of bank card names. With cashback taken out of the index entirely, the UK jump shrinks by about a third but is still clearly there.

**"If voucher codes went down, why did cashback go up?"**
They measure different things over different periods. "Voucher code" fell from 2019 to 2025 because people started saying "discount code" instead (that rose over the same years). In 2026 every guaranteed reward went up together: voucher codes, cashback, loyalty points, free gifts. I left voucher codes out of the prize-vs-guaranteed comparison for that reason, and the results hold with or without them.

**"Why compare with 2019?"**
It's the last normal year before COVID. Comparing whole years, or the same months each year, stops Black Friday and other seasonal peaks skewing it.

**"Did AI just do this for you?"**
Claude labelled the 669 searches and helped write the code. To check its labels, I trained a separate model on them (91% agreement) and compared it with keyword rules (73%). The questions and the judgement on what the data can't say were the hard part. *(Only use this if you've read the README's design decisions and can talk through them.)*

**"What would you do with this in a promotions brief?"**
After a sudden shock, lead with a guaranteed reward and use the prize as the upsell. In a slow squeeze, prize mechanics hold up, so the big headline prize still earns its place.

## First comment (pin it)

Code, data and full method: github.com/Osman246/certainty-vs-chance

The README opens with a one-minute summary. The regression, the placebo tests and the ML are underneath.

---

## The video (47 seconds, 1080×1350, built from the data by `video/render.py`)

It works muted: every slide says in words what it shows. If you add a voiceover, record it yourself (no AI voice, no stock music) and keep to these lines:

| Time | Slide | Optional voiceover |
|---|---|---|
| 0-4 s | "£5 guaranteed, or a shot at £5,000?" | "Guaranteed fiver, or a shot at five grand?" |
| 4-8 s | When money gets tight, what do we want? 32 terms, 94 months, 669 searches | "Eight years of searches in the UK and the UAE. Same war, two routes: the UAE was hit directly, the UK through energy prices." |
| 8-15 s | In a slow squeeze, we chased prizes | "Before 2026, prize searches rose 57%. Guaranteed rewards, just 15%." |
| 15-22 s | Then a sudden shock swung it back | "Then the energy shock hit. Within a month, cashback searches were twice their winter level." |
| 22-29 s | Same months, every year. Only 2026 stands out | "And that's not just the time of year. 2026 was almost three times any year since 2019." |
| 29-36 s | UK vs UAE: same shock, different speed | "Same war in the UAE, hit directly. Cashback searches climbed for months instead of jumping. Both turned to guaranteed rewards; the UK just did it faster." |
| 36-42 s | How it was built | "Claude labelled the searches, a simple model checked its work, and the stats are on GitHub." |
| 42-47 s | Guaranteed £5, or a shot at £5,000? | "So, which would you take?" |

- Upload it natively to LinkedIn. The first frame already shows the question, so it works as the thumbnail.
- Watch it once on your phone, muted, before posting.
