<!-- build-plan:begin -->
## Active build plan — shapelid_devportal_agent
Work through every step, and confirm each is satisfied before telling the user the agent is ready.

- [ ] Create entities: ApiKey, Developer, ApiTier, UsageLog, WebhookEndpoint, ApiDocumentationPage in the Developer Portal app
- [ ] Create backend functions: generateApiKey, validateApiKey, enforceRateLimit, logApiUsage, upgradeDeveloperTier, revokeApiKey, listDeveloperUsage, searchMaterialsApi, searchManufacturersApi, createQuoteApi, createOrderApi, uploadAndAnalyzeApi, publishDocsUpdate
- [ ] Write operating rules to .agents/rules/security.md
- [ ] Write operating rules to .agents/rules/tier-governance.md
- [ ] Write operating rules to .agents/rules/data-handling.md
- [ ] Write operating rules to .agents/rules/escalation.md
- [ ] Write skills to .agents/skills/provision-api-key.md
- [ ] Write skills to .agents/skills/developer-support-triage.md
- [ ] Write skills to .agents/skills/upgrade-tier.md
- [ ] Write skills to .agents/skills/generate-usage-digest.md
- [ ] Write skills to .agents/skills/docs-deploy-check.md
- [ ] Write skills to .agents/skills/handle-abuse.md
- [ ] Authorize the GitHub connector
- [ ] Authorize the Slack bot connector
- [ ] Set up Slack channel: #developer-portal for inbound @mentions and outbound notifications
- [ ] Configure GitHub webhook on shapelid-client-portal repo for docs.json push events
- [ ] Set up the Slack @mention automation
- [ ] Set up the ApiKey usage threshold automation
- [ ] Set up the New Developer registered automation
- [ ] Set up the PayTR subscription callback automation
- [ ] Set up the docs.json push automation
- [ ] Set up the weekly usage digest cron automation
- [ ] Deploy Mintlify custom domain config for developers.shapelid.com
- [ ] Test end-to-end: create a test Developer → provision key → call a protected endpoint → verify rate limiting and usage logging
<!-- build-plan:end -->