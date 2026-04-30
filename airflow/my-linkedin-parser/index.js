const express = require('express');
const { ApifyClient } = require('apify-client');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// --- CONFIG ---
const APIFY_TOKEN = 'apify_api_JURUV2L39k9ngFhqQRHQhDAV2qCxkL0PPzjG';
const client = new ApifyClient({ token: APIFY_TOKEN });

// Folder for Airflow
const storageDir = path.join(__dirname, 'scraped_data');
if (!fs.existsSync(storageDir)) {
    fs.mkdirSync(storageDir);
}

/**
 * Enhanced cleaning function with deep fallback logic for Certifications
 */
const cleanProfileData = (rawItem) => {
    const rawCerts = rawItem.certifications || rawItem.licensesAndCertifications || rawItem.licenses || [];

    return {
        id: rawItem.id || rawItem.objectUrn,
        fullName: `${rawItem.firstName || ''} ${rawItem.lastName || ''}`.trim() || rawItem.name,
        linkedinUrl: rawItem.linkedinUrl || rawItem.url,
        headline: rawItem.headline,
        location: rawItem.location?.parsed?.text || rawItem.location?.linkedinText || "Unknown",
        
        experience: (rawItem.experience || []).map(exp => ({
            title: exp.position || exp.title,
            company: exp.companyName,
            start: exp.startDate?.text || 'N/A',
            end: exp.endDate?.text || 'Present'
        })),

        education: (rawItem.education || rawItem.profileTopEducation || []).map(edu => ({
            school: edu.schoolName || edu.school,
            degree: edu.degree,
            period: edu.period || (edu.startDate ? `${edu.startDate.text} - ${edu.endDate?.text || ''}` : 'N/A')
        })),

        // --- DEEP MAPPING FOR CERTIFICATIONS ---
        certifications: rawCerts.map(cert => ({
            name: cert.name || cert.title || "Unknown Certificate",
            // Check every possible place LinkedIn stores the issuing organization
            authority: cert.authority || cert.issuingOrganizationName || cert.issuingOrganization?.name || cert.issuer || "N/A",
            // Check multiple date formats
            issued: cert.startDate?.text || cert.issueDate || cert.issuedAt || "N/A",
            url: cert.url || cert.credentialUrl || cert.link || null
        })),

        skills: (rawItem.skills || []).map(s => (typeof s === 'string' ? s : (s.name || s.title))),
        scrapedAt: new Date().toISOString()
    };
};

app.get('/', (req, res) => {
    res.send(`
        <body style="font-family:sans-serif; text-align:center; padding-top:50px; background:#f4f7f9;">
            <div style="background:white; display:inline-block; padding:40px; border-radius:15px; box-shadow:0 5px 15px rgba(0,0,0,0.1);">
                <h2 style="color:#0a66c2;">LinkedIn Scraper (Final Mapping Fix)</h2>
                <p>Status: Deep-mapping for Certificates enabled 🛠️</p>
                <form action="/parse" method="POST">
                    <input type="text" name="url" placeholder="Paste Profile URL" style="width:380px; padding:12px; border:1px solid #ccc; border-radius:5px;" required />
                    <button type="submit" style="padding:12px 25px; background:#0a66c2; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; margin-top:10px;">Run Deep Extract</button>
                </form>
            </div>
        </body>
    `);
});

app.post('/parse', async (req, res) => {
    try {
        const profileUrl = req.body.url;
        console.log(`[START] Scraping profile: ${profileUrl}`);

        const input = {
            "urls": [profileUrl],
            "proxyConfiguration": { "useApifyProxy": true }
        };

        const run = await client.actor("harvestapi/linkedin-profile-scraper").call(input);
        const { items } = await client.dataset(run.defaultDatasetId).listItems();

        if (items.length === 0) return res.status(404).send("No data found.");

        const cleanedData = cleanProfileData(items[0]);

        // Save to JSON
        const safeName = cleanedData.fullName.replace(/[^a-z0-9]/gi, '_').toLowerCase();
        const fileName = `profile_${safeName}.json`;
        const filePath = path.join(storageDir, fileName);
        
        fs.writeFileSync(filePath, JSON.stringify(cleanedData, null, 2));
        console.log(`[SUCCESS] Saved: ${fileName}`);

        res.send(`
            <body style="font-family:sans-serif; padding:20px; background:#f4f7f9;">
                <h3 style="color:#0a66c2;">✅ Full Data Extracted</h3>
                <p>JSON Saved: <code>${fileName}</code></p>
                <div style="text-align:left; background:#222; color:#0f0; padding:20px; border-radius:10px; overflow:auto; max-height:600px;">
                    <pre>${JSON.stringify(cleanedData, null, 2)}</pre>
                </div>
                <br><a href="/">Back</a>
            </body>
        `);

    } catch (err) {
        console.error("[ERROR]", err.message);
        res.status(500).send(`Error: ${err.message}`);
    }
});

// JSON API endpoint for the FastAPI backend
app.post('/api/parse', async (req, res) => {
    try {
        const profileUrl = req.body.url;
        if (!profileUrl) return res.status(400).json({ error: 'url is required' });

        const input = {
            "urls": [profileUrl],
            "proxyConfiguration": { "useApifyProxy": true }
        };

        const run = await client.actor("harvestapi/linkedin-profile-scraper").call(input);
        const { items } = await client.dataset(run.defaultDatasetId).listItems();

        if (items.length === 0) return res.status(404).json({ error: 'No data found' });

        const cleanedData = cleanProfileData(items[0]);
        res.json(cleanedData);
    } catch (err) {
        console.error("[ERROR /api/parse]", err.message);
        res.status(500).json({ error: err.message });
    }
});

const PORT = 3000;
app.listen(PORT, () => console.log(`🚀 Service ready at http://localhost:${PORT}`));