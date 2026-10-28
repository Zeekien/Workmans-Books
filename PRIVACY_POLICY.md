# Privacy Policy for Work-Man's Books

**Last Updated**: March 30, 2026

**Work-Man's Books** ("Application", "We", "Us", or "Our") is committed to protecting your privacy. This Privacy Policy explains how personal, client, and financial information is collected, used, stored, and protected when you use the Application, including when you integrate with third-party services such as Intuit QuickBooks Online.

---

## 1. Information We Collect

### 1.1 Information You Provide Directly
When using Work-Man's Books, you may enter the following data directly into the Application:
- **Client Information**: Client names, phone numbers, email addresses, and service addresses.
- **Job & Service Details**: Job titles, schedules, add-on selections, estimated hours, and estimated costs.
- **Invoice & Financial Data**: Created invoices, hours worked, total charges, and transaction dates.

### 1.2 Intuit QuickBooks Integration Data
If you choose to connect Work-Man's Books with your Intuit QuickBooks Online account, the Application accesses the following data via Intuit's OAuth 2.0 API:
- **OAuth Authentication Tokens**: Encrypted access tokens and refresh tokens required to authenticate API requests on your behalf.
- **QuickBooks Accounting Data**: Customer records, invoice details, and sync status necessary to mirror your local Work-Man's Books records in your QuickBooks Online accounting account.

---

## 2. On-Device Local Data Storage Policy

### 2.1 Local Storage
Work-Man's Books operates with an **on-device local architecture**. All database records (`main.db`), client profiles, invoice histories, and encrypted OAuth tokens are stored locally on your mobile device.

### 2.2 No External Cloud Servers
We do not host or operate remote external servers that copy, aggregate, or store your business or client data. All sync requests travel directly between your mobile device and Intuit's secure servers (`api.intuit.com`) via encrypted HTTPS/TLS 1.2+ connections.

---

## 3. How We Use Your Information

We use the information collected solely to provide and improve the functionality of Work-Man's Books, specifically:
- Managing client profiles and job scheduling.
- Generating invoices and computing project totals.
- Synchronizing client and invoice records with your Intuit QuickBooks Online account (when enabled).
- Authenticating your connection with Intuit using OAuth 2.0.

---

## 4. STRICT NON-DISCLOSURE & NON-SALE OF DATA

**WE DO NOT SELL, RENT, LEASE, OR TRADE YOUR PERSONAL OR FINANCIAL DATA.**

Your data—including all data accessed from or synchronized with Intuit QuickBooks—will **NEVER** be sold or shared with third parties, advertisers, data brokers, or marketing networks.

---

## 5. Intuit Data Access, Retention & Token Revocation

### 5.1 Token Storage & Expiration
OAuth 2.0 access tokens and refresh tokens granted by Intuit are stored securely in local app storage. Access tokens expire after 60 minutes and are automatically refreshed. Refresh tokens expire after 100 days or upon user disconnect.

### 5.2 Disconnecting Intuit QuickBooks
You may disconnect Work-Man's Books from your QuickBooks account at any time by:
1. Navigating to **Settings -> Intuit QuickBooks Integration** in the Application and tapping **Disconnect**.
2. Or revoking access directly inside your **Intuit Account Management -> Connected Apps** portal.

Upon disconnect, the Application immediately purges all stored OAuth tokens from your local database and revokes the active token via Intuit's token revocation API (`https://developer.api.intuit.com/v1/oauth2/tokens/revoke`).

---

## 6. Data Security Measures

We take reasonable technical and administrative precautions to protect your data, including:
- **Transport Encryption**: All communication with Intuit QuickBooks APIs is encrypted using TLS 1.2 or higher.
- **Local Protection**: Relying on Android system-level sandboxing, device encryption, and secure local file storage.
- **Minimal Access Scopes**: Requesting only necessary QuickBooks API scopes (`com.intuit.quickbooks.accounting`).

---

## 7. User Data Controls & Deletion

Since your data is stored locally on your device:
- **Modification & Deletion**: You can edit or delete client records, jobs, and invoices at any time directly within the Application.
- **Complete Data Wipe**: Uninstalling the Application or using the device application data clear feature permanently deletes all local application databases and stored tokens.

---

## 8. Changes to This Privacy Policy

We may update this Privacy Policy periodically to reflect app updates or legal requirements. Updated versions will be published with a revised "Last Updated" date.

---

## 9. Contact Us

If you have questions or concerns about this Privacy Policy or your data privacy, please contact us at:

- **Application Name**: Work-Man's Books
- **Developer Contact**: `support@workmansbooks.com` (or official application support contact)
