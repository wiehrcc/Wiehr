const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

const SRC = path.join(__dirname, 'geodata', 'ETOPO5.DAT');
const OUT_PNG = path.join(__dirname, '..', 'web', 'static', 'images', 'atlas-terrain.png');
const OUT_META = path.join(__dirname, '..', 'web', 'static', 'js', 'atlas-terrain-meta.js');

const SRC_W = 4320, SRC_H = 2160;

const OUT_W = parseInt(process.env.TW || '1620', 10);
const OUT_H = parseInt(process.env.TH || '810', 10);

function crc32(buf) {
    let c, crc = 0xffffffff;
    for (let n = 0; n < buf.length; n++) {
        c = (crc ^ buf[n]) & 0xff;
        for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
        crc = c ^ (crc >>> 8);
    }
    return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
    const len = Buffer.alloc(4);
    len.writeUInt32BE(data.length, 0);
    const typeBuf = Buffer.from(type, 'ascii');
    const body = Buffer.concat([typeBuf, data]);
    const crcBuf = Buffer.alloc(4);
    crcBuf.writeUInt32BE(crc32(body), 0);
    return Buffer.concat([len, body, crcBuf]);
}

function encodeGrayAlphaPNG(width, height, pixels) {
    const sig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(width, 0);
    ihdr.writeUInt32BE(height, 4);
    ihdr[8] = 8;
    ihdr[9] = 4;
    ihdr[10] = 0;
    ihdr[11] = 0;
    ihdr[12] = 0;

    const bpp = 2;
    const stride = width * bpp;
    const raw = Buffer.alloc((stride + 1) * height);

    const cand = [Buffer.alloc(stride), Buffer.alloc(stride), Buffer.alloc(stride),
                  Buffer.alloc(stride), Buffer.alloc(stride)];

    function paeth(a, b, c) {
        const p = a + b - c;
        const pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
        if (pa <= pb && pa <= pc) return a;
        if (pb <= pc) return b;
        return c;
    }

    for (let y = 0; y < height; y++) {
        const cur = y * stride;
        const prev = (y - 1) * stride;
        for (let i = 0; i < stride; i++) {
            const x = pixels[cur + i];
            const a = i >= bpp ? pixels[cur + i - bpp] : 0;
            const b = y === 0 ? 0 : pixels[prev + i];
            const c = (y === 0 || i < bpp) ? 0 : pixels[prev + i - bpp];
            cand[0][i] = x;
            cand[1][i] = (x - a) & 0xff;
            cand[2][i] = (x - b) & 0xff;
            cand[3][i] = (x - ((a + b) >> 1)) & 0xff;
            cand[4][i] = (x - paeth(a, b, c)) & 0xff;
        }

        let best = 0, bestScore = Infinity;
        for (let f = 0; f < 5; f++) {
            let score = 0;
            const buf = cand[f];
            for (let i = 0; i < stride; i++) {
                const v = buf[i];
                score += v < 128 ? v : 256 - v;
            }
            if (score < bestScore) { bestScore = score; best = f; }
        }

        const rowStart = y * (stride + 1);
        raw[rowStart] = best;
        cand[best].copy(raw, rowStart + 1);
    }

    const idat = zlib.deflateSync(raw, { level: 9 });

    return Buffer.concat([
        sig,
        chunk('IHDR', ihdr),
        chunk('IDAT', idat),
        chunk('IEND', Buffer.alloc(0)),
    ]);
}

function main() {
    const buf = fs.readFileSync(SRC);
    if (buf.length !== SRC_W * SRC_H * 2) {
        throw new Error('unexpected ETOPO5 size: ' + buf.length);
    }

    const elev = new Int16Array(SRC_W * SRC_H);
    for (let i = 0; i < elev.length; i++) elev[i] = buf.readInt16BE(i * 2);

    function elevAt(col, row) {
        if (row < 0) row = 0;
        if (row >= SRC_H) row = SRC_H - 1;
        const c = ((col % SRC_W) + SRC_W) % SRC_W;
        return elev[row * SRC_W + c];
    }

    const pixels = Buffer.alloc(OUT_W * OUT_H * 2);

    const colShift = SRC_W / 2;

    let minE = Infinity, maxE = -Infinity, landCount = 0;

    const sxRatio = SRC_W / OUT_W, syRatio = SRC_H / OUT_H;
    const boxW = Math.max(1, Math.round(sxRatio)), boxH = Math.max(1, Math.round(syRatio));

    function sampleElev(col, row) {
        if (boxW === 1 && boxH === 1) return elevAt(col, row);
        let sum = 0, n = 0;
        for (let by = 0; by < boxH; by++) {
            for (let bx = 0; bx < boxW; bx++) {
                sum += elevAt(col + bx, row + by);
                n++;
            }
        }
        return sum / n;
    }

    for (let y = 0; y < OUT_H; y++) {
        for (let x = 0; x < OUT_W; x++) {
            const srcCol = Math.round(x * sxRatio) + colShift;
            const srcRow = Math.round(y * syRatio);

            const e = sampleElev(srcCol, srcRow);
            if (e < minE) minE = e;
            if (e > maxE) maxE = e;

            let alpha = 0;
            if (e > 0) {
                landCount++;
                const t = Math.min(1, e / 5000);
                let a = 0.18 + 0.72 * Math.pow(t, 0.5);

                const eE = sampleElev(srcCol + boxW, srcRow);
                const eN = sampleElev(srcCol, srcRow - boxH);
                const dzdx = (Math.max(0, eE) - e) / (700 * sxRatio);
                const dzdy = (Math.max(0, eN) - e) / (700 * syRatio);
                const illum = -(dzdx * -0.6 + dzdy * 0.8);
                a += Math.max(-0.20, Math.min(0.20, illum));

                alpha = Math.max(0, Math.min(255, Math.round(a * 255)));
            }

            const o = (y * OUT_W + x) * 2;
            pixels[o] = 0;
            pixels[o + 1] = alpha;
        }
    }

    const png = encodeGrayAlphaPNG(OUT_W, OUT_H, pixels);
    fs.mkdirSync(path.dirname(OUT_PNG), { recursive: true });
    fs.writeFileSync(OUT_PNG, png);

    const meta = 'const atlasTerrainMeta={width:' + OUT_W + ',height:' + OUT_H +
        ',lonMin:-180,lonMax:180,latMin:-90,latMax:90};\n';
    fs.writeFileSync(OUT_META, meta, 'utf8');

    const stats = fs.statSync(OUT_PNG);
    console.log('source elevation range:', minE, '..', maxE, 'm');
    console.log('land pixels:', landCount, '(' + (landCount / (OUT_W * OUT_H) * 100).toFixed(1) + '%)');
    console.log('PNG:', OUT_W + 'x' + OUT_H, '->', (stats.size / 1024 / 1024).toFixed(2), 'MB');
}

main();
