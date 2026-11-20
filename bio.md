I'm Ruslan, a second-year Computer Science student at PJATK in Warsaw, heading into security engineering and DevOps. I like tools that watch a system, map what is exposed and raise an alert when something looks wrong.

**What I've built so far**

- **osint-recon** ([web-crawler](https://github.com/mvrhaa/web-crawler)): an async reconnaissance crawler that maps a site's pages, emails, subdomains and tech stack. A scope guard checks every request and every redirect hop, robots.txt is respected, and on its own test range it finds all 43 planted artifacts.
- **log-watcher**: a CLI that parses nginx access logs and SSH auth logs, counts failed logins per IP and exits with code 1 once an IP crosses the threshold, so a cron job or a CI pipeline can raise the alarm. Runs in Docker, tested in GitHub Actions.
- **[minibank](https://github.com/mvrhaa/minibank)**: a banking REST API on Spring Boot with Spring Security and PostgreSQL, started with Docker Compose.
- **[brokenlinkchecker](https://github.com/mvrhaa/brokenlinkchecker)**: a multithreaded Java crawler that finds broken links.

**Tools:** Python, Java, Docker, GitHub Actions, PostgreSQL, Spring Security, Playwright.

Outside security I build quant models ([curvelq](https://github.com/mvrhaa/curvelq)), and with my team I won the Quantum Optimization track at IBM Qiskit Fall Fest 2026.

The graph above is built from my public repositories and redraws itself when I publish a new one.
