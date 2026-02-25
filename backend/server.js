
const express = require('express');
const axios = require('axios');
const cors = require('cors');

const path = require('path');
const fs = require('fs');

const app = express();
app.use(cors());
app.use(express.json());

// Serve static files from the frontend directory
app.use(express.static(path.join(__dirname, '../frontend')));

const { exec, spawn } = require('child_process');

// Route to proxy downloads and force "attachment" header using yt-dlp streaming
app.get('/proxy-download', async (req, res) => {
    const { url, filename, formatId } = req.query;

    if (!url) {
        return res.status(400).send("URL is required");
    }

    // Set headers to force download
    const safeFilename = (filename || `download-${Date.now()}.mp4`).replace(/[^a-z0-9._-]/gi, '_');
    res.setHeader('Content-Disposition', `attachment; filename="${safeFilename}"`);
    res.setHeader('Content-Type', 'application/octet-stream');

    console.log(`Starting stream for: ${url} (formatId: ${formatId || 'best'})`);

    // Use yt-dlp to stream the video directly to stdout
    const args = ['-m', 'yt_dlp', '-o', '-', '--no-cache-dir', url];
    if (formatId) {
        args.push('-f', formatId);
    }

    const downloader = spawn('python', args, { shell: true });

    downloader.stdout.pipe(res);

    downloader.stderr.on('data', (data) => {
        console.error(`yt-dlp stderr: ${data}`);
    });

    downloader.on('error', (err) => {
        console.error(`Failed to start downloader: ${err.message}`);
    });

    downloader.on('close', (code) => {
        if (code !== 0) {
            console.error(`yt-dlp process exited with code ${code}`);
            if (!res.headersSent) {
                res.status(500).send("Failed to stream file");
            }
        }
    });

    req.on('close', () => {
        console.log("Client disconnected, killing yt-dlp");
        downloader.kill();
    });
});

app.post('/download', async (req, res) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ error: "URL is required" });
    }

    try {
        // Use yt-dlp to get video information
        const command = `python -m yt_dlp -j "${url}"`;
        exec(command, (error, stdout, stderr) => {
            if (error) {
                console.error("yt-dlp error:", stderr);
                return res.status(500).json({ error: "Failed to process URL with yt-dlp" });
            }

            try {
                const info = JSON.parse(stdout);

                // Filter and map formats for easier use in frontend
                const formats = info.formats
                    .filter(f => f.url && (f.vcodec !== 'none' || f.acodec !== 'none'))
                    .map(f => ({
                        formatId: f.format_id,
                        ext: f.ext,
                        resolution: f.resolution || (f.width ? `${f.width}x${f.height}` : 'unknown'),
                        filesize: f.filesize || f.filesize_approx,
                        url: f.url,
                        note: f.format_note || '',
                        isImproved: f.vcodec !== 'none' && f.acodec !== 'none' // Has both video and audio
                    }))
                    .sort((a, b) => (b.height || 0) - (a.height || 0)); // Sort by resolution

                res.json({
                    type: info.extractor || "generic",
                    title: info.title,
                    thumbnail: info.thumbnail,
                    formats: formats,
                    originalUrl: info.original_url
                });
            } catch (parseError) {
                console.error("JSON parse error:", parseError);
                res.status(500).json({ error: "Failed to parse metadata" });
            }
        });
    } catch (err) {
        console.error("Error processing URL:", err);
        res.status(500).json({ error: "Failed to process URL" });
    }
});

app.listen(5000, () => console.log("Server running on port 5000"));
