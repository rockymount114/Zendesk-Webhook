


ZENDESK ENDPOINT


***get tickets url {ZENDESK_BASE_URL}/api/v2/tickets.json***

ticket sample json as ticket_4021.json

***get ticket comments url {ZENDESK_BASE_URL}/tickets/{ticket_id}/comments.json***

comments sample json as ticket_4021_comments.json

***get users url {ZENDESK_BASE_URL}/users/{user_id}.json***


1. Open **@prompt_plan.md** and identify any prompts not marked as completed.
2. For each incomplete prompt:
    - Double-check if it's truly unfinished (if uncertain, ask for clarification).
    - If you confirm it's already done, skip it.
    - Otherwise, implement it as described.
    - Make sure the tests pass, and the program builds/runs
    - Commit the changes to your repository with a clear commit message.
    - Update **@prompt_plan.md** to mark this prompt as completed.
3. After you finish each prompt, pause and wait for user review or feedback.
4. Repeat with the next unfinished prompt as directed by the user.

## Design Context

### Users
Anyone with the application URL. Users should sign in before reaching the Zendesk ticket-monitoring interface. The interface should make it easy to review recent tickets, open tickets, and ticket KPIs.

### Brand Personality
City of Rocky Mount; clear, compact, and delightful.

### Aesthetic Direction
Use a compact, polished, Apple-inspired visual style. Keep the light presentation and responsive layout, with a clear civic-service identity rather than a generic admin template.

### Design Principles
- Make ticket monitoring and common actions easy to understand at a glance.
- Use compact layouts without sacrificing readable type, clear labels, or touch-friendly controls.
- Make ticket status and priority clear through text and color, not color alone.
- Keep the interface polished and welcoming, with restrained visual effects and purposeful motion.
- Treat sign-in as the entry point to the ticket dashboard; keep the authenticated experience consistent across its pages.