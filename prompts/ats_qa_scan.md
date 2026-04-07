Act as both an ATS parser and a hiring manager doing a 10-second CV screen.

Review the tailored CV against the job description.

Return structured output under these headings only:

1. ATS Compatibility Score
- Score from 1 to 100.
- Explain briefly.

2. Recruiter First-Impression Score
- Score from 1 to 10.
- Explain what is clear immediately and what is not.

3. Keyword Coverage
- Which critical keywords are present.
- Which important ones are still missing.
- Which are overused or inserted unnaturally.

4. Narrative and Positioning Check
- Is the target role clear at first glance?
- Is the value proposition distinctive?
- Does the CV feel tailored or generic?

5. Chronology and Structure Check
- Check date consistency, career progression, section order, and clarity of role transitions.

6. Achievement Quality Check
- Are the bullets specific, credible, and results-oriented?
- Flag any bullets that still feel task-based or vague.

7. Seniority Alignment Check
- Does the CV read at the right level for the role?
- Flag under-selling or over-selling.

8. Authenticity and AI-Risk Check
- Does any section sound generic, formulaic, keyword-stuffed, or obviously AI-written?
- Quote exact examples.

9. ATS Parsing Risk Check
- Flag formatting, heading, punctuation, layout, or structure issues that could hurt parsing.

10. Rejection Risks
- List anything that could cause the CV to be screened out quickly.

11. Exact Final Changes Required
- Give the smallest set of specific edits needed to materially improve the CV.

Rules:
- Be strict.
- Do not praise weak content.
- Do not suggest adding skills or achievements unless supported by the CV.
- Prioritise practical fixes that improve both ATS performance and human readability.
