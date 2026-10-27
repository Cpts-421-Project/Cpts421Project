-- Curated Ancient Workers from The British Museum
-- Idempotent SQL script for database population
BEGIN;

INSERT INTO sources (citation_text)
SELECT 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'
WHERE NOT EXISTS (SELECT 1 FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.');

-- Wall painting fragment, Tomb-chapel of Nebamun: Inspecting Cattle and Herdsmen (British Museum: EA37976)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Wall painting fragment, Tomb-chapel of Nebamun: Inspecting Cattle and Herdsmen', 'Plaster, pigment, mud plaster', 'Tomb-chapel of Nebamun, Dra Abu el-Naga, Thebes, Upper Egypt', 'EA37976', 'Fragment of a polychrome tomb painting from the Tomb-chapel of Nebamun at Thebes. Nebamun, scribe and grain accountant at the Temple of Amun, inspects herds of cattle brought before him. Herdsmen lead and present long-horned and hornless oxen, while an elderly, balding herdsman kneels before Nebamun offering obeisance. Scribes with papyrus rolls and reed pens stand by to record the official livestock count. The hieroglyphic captions record the dialogue of the herdsmen praising Nebamun.',
        'ca. 1350 BCE', -1350, -1350, 58.5, 105.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA37976.jpg'
FROM objects o WHERE o.inventory_number = 'EA37976'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA37976.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Animal Husbandry') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Animal Husbandry'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Scribes') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Scribes'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tomb-of-Nebamun') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tomb-of-Nebamun'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('New Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'New Kingdom'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Labor'
WHERE o.inventory_number = 'EA37976'
ON CONFLICT DO NOTHING;

-- Wall painting fragment, Tomb-chapel of Nebamun: Counting Geese and Poultry (British Museum: EA37978)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Wall painting fragment, Tomb-chapel of Nebamun: Counting Geese and Poultry', 'Plaster, pigment, mud plaster', 'Tomb-chapel of Nebamun, Dra Abu el-Naga, Thebes, Upper Egypt', 'EA37978', 'Fragment of a painted limestone wall panel from the Tomb-chapel of Nebamun depicting the counting of domesticated geese and waterfowl. Agricultural laborers and poultry keepers present flocks of white and grey geese; one herdsman holds open a wicker basket coop while other birds are lined up in registers. Scribes bow and present inscribed papyrus scrolls recording the exact tally for the estate accounts.',
        'ca. 1350 BCE', -1350, -1350, 71.0, 115.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA37978.jpg'
FROM objects o WHERE o.inventory_number = 'EA37978'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA37978.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Poultry') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Poultry'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Scribes') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Scribes'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tomb-of-Nebamun') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tomb-of-Nebamun'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('New Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'New Kingdom'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Labor'
WHERE o.inventory_number = 'EA37978'
ON CONFLICT DO NOTHING;

-- Wall painting fragment, Tomb-chapel of Nebamun: Assessing the Crops of the Estates (British Museum: EA37977)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Wall painting fragment, Tomb-chapel of Nebamun: Assessing the Crops of the Estates', 'Plaster, pigment, mud plaster', 'Tomb-chapel of Nebamun, Dra Abu el-Naga, Thebes, Upper Egypt', 'EA37977', 'Polychrome wall painting from the Tomb-chapel of Nebamun illustrating estate agricultural administration. Estate workers and farmers gather to report on crop yields. Scribes hold writing tablets and recording palettes, verifying measurements and recording the harvest figures for the grain stores of the Amun temple complex.',
        'ca. 1350 BCE', -1350, -1350, 41.0, 91.0, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA37977.jpg'
FROM objects o WHERE o.inventory_number = 'EA37977'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA37977.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Grain') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Grain'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Estate Administration') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Estate Administration'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tomb-of-Nebamun') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tomb-of-Nebamun'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('New Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'New Kingdom'
WHERE o.inventory_number = 'EA37977'
ON CONFLICT DO NOTHING;

-- Wall painting fragment, Tomb-chapel of Nebamun: Surveying the Fields and Harvesting Grain (British Museum: EA37982)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Wall painting fragment, Tomb-chapel of Nebamun: Surveying the Fields and Harvesting Grain', 'Plaster, pigment, mud plaster', 'Tomb-chapel of Nebamun, Dra Abu el-Naga, Thebes, Upper Egypt', 'EA37982', 'Painted wall fragment from the Tomb-chapel of Nebamun showing agricultural field work and cadastral surveying. In the lower register, field laborers reap tall ripe emmer wheat using curved sickles. In the upper register, surveyors stretch a knotted measuring rope across the fields to assess agricultural boundaries and tax liabilities. A chariot with two spirited horses and an attendant rests beneath the shade of a sycamore fig tree.',
        'ca. 1350 BCE', -1350, -1350, 44.5, 61.0, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA37982.jpg'
FROM objects o WHERE o.inventory_number = 'EA37982'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA37982.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Harvest') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Harvest'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Field Surveyors') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Field Surveyors'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tomb-of-Nebamun') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tomb-of-Nebamun'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('New Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'New Kingdom'
WHERE o.inventory_number = 'EA37982'
ON CONFLICT DO NOTHING;

-- Wall painting detail, Tomb-chapel of Nebamun: The Scribe of Accounts (British Museum: EA37979)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Wall painting detail, Tomb-chapel of Nebamun: The Scribe of Accounts', 'Plaster, pigment, mud plaster', 'Tomb-chapel of Nebamun, Dra Abu el-Naga, Thebes, Upper Egypt', 'EA37979', 'Close detail of an ancient Egyptian scribe from the Tomb-chapel of Nebamun. The scribe is depicted seated cross-legged on a mat with a long unrolled papyrus document across his lap, dipping a reed brush into an ink palette containing cakes of black and red ink. Scribes formed the administrative backbone of ancient Egyptian labor, recording rations, work quotas, estate yields, and artisan assignments.',
        'ca. 1350 BCE', -1350, -1350, 38.0, 42.0, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA37979.jpg'
FROM objects o WHERE o.inventory_number = 'EA37979'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA37979.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Scribes') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Scribes'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Administration') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Administration'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Writing') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Writing'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tomb-of-Nebamun') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tomb-of-Nebamun'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('New Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'New Kingdom'
WHERE o.inventory_number = 'EA37979'
ON CONFLICT DO NOTHING;

-- Model, river boat with rowers and sailors (British Museum: EA36422)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, river boat with rowers and sailors', 'Wood, pigment, linen cord', 'Beni Hasan, Middle Egypt', 'EA36422', 'Painted wooden tomb model of a Nile transport boat manned by a crew of rowers, deckhands, and a steersman operating a large steering oar. Transport along the Nile was essential for ancient Egyptian trade, grain distribution, stone transport for monuments, and troop movements. Such models were placed in Middle Kingdom tombs to ensure transportation in the afterlife.',
        'ca. 1900 BCE', -1900, -1900, 28.0, 14.0, 68.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_EA36422.jpg'
FROM objects o WHERE o.inventory_number = 'EA36422'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_EA36422.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Maritime') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Maritime'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Boats') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Boats'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Rowers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Rowers'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Middle Kingdom') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Middle Kingdom'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Transportation') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Transportation'
WHERE o.inventory_number = 'EA36422'
ON CONFLICT DO NOTHING;

-- Attic black-figure neck-amphora: The Olive Harvest (British Museum: 1837,0609.42)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Attic black-figure neck-amphora: The Olive Harvest', 'Terracotta (clay)', 'Vulci, Etruria (produced in Athens, Greece)', '1837,0609.42', 'Attic black-figure amphora attributed to the Antimenes Painter depicting the olive harvest, one of the most famous Greek representations of agricultural labor. In an olive grove, two men have climbed into the branches of an olive tree and beat the boughs with long poles to knock ripe olives loose. A bearded man at the base strikes the trunk, while a naked youth scrambles on his knees on the ground collecting olives into a deep woven wicker basket.',
        'ca. 520 BCE', -520, -520, 40.6, 27.0, 27.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1837_0609_42.jpg'
FROM objects o WHERE o.inventory_number = '1837,0609.42'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1837_0609_42.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Olive Harvest') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Olive Harvest'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Pottery') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Pottery'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Black-Figure') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Black-Figure'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Antimenes Painter') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Antimenes Painter'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Labor'
WHERE o.inventory_number = '1837,0609.42'
ON CONFLICT DO NOTHING;

-- Attic black-figure eye-kylix: Potter at Work on the Wheel (British Museum: 1847,1125.18)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Attic black-figure eye-kylix: Potter at Work on the Wheel', 'Terracotta (clay)', 'Attica, Greece', '1847,1125.18', 'Attic black-figure eye-kylix (Type A, Cat. Vases B 432). The interior tondo depicts an ancient Greek potter seated beside a low turntable wheel, carefully assembling a kylix and attaching a clay handle. Behind him on a workshop wall shelf are arranged four finished kylikes and an oinochoe jug drying before firing. Exterior features large protective eyes and Athena fighting a giant in gigantomachy.',
        'ca. 520–480 BCE', -520, -480, 8.9, 20.3, 20.3, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1847_1125_18.jpg'
FROM objects o WHERE o.inventory_number = '1847,1125.18'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1847_1125_18.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Pottery') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Pottery'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ceramics') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ceramics'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Crafts') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Crafts'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Potter') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Potter'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Workshop') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Workshop'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Black-Figure') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Black-Figure'
WHERE o.inventory_number = '1847,1125.18'
ON CONFLICT DO NOTHING;

-- Attic white-ground alabastron: Signed by Master Potter Pasiades (British Museum: 1887,0801.61)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Attic white-ground alabastron: Signed by Master Potter Pasiades', 'Terracotta (white-ground clay)', 'Marion-Arsinoe (Tomb 162), Cyprus (produced in Athens, Greece)', '1887,0801.61', 'Attic white-ground perfume flask (alabastron, Cat. Vases B 668) featuring the signature of the master potter Pasiades: ''PASIADES EPOIESEN'' (''Pasiades made it'') stamped onto the mouth. Decorated by the Pasiades Painter with a heron standing between two running maenads. Signed ceramic vessels illustrate the pride and social standing of Athenian ceramic workshop proprietors and master craftsmen.',
        'ca. 510 BCE', -510, -510, 14.6, 4.8, 4.8, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1887_0801_61.jpg'
FROM objects o WHERE o.inventory_number = '1887,0801.61'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1887_0801_61.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Pottery') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Pottery'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Artisans') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Artisans'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Master Potter') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Master Potter'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Pasiades') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Pasiades'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Signatures') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Signatures'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('White-Ground') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'White-Ground'
WHERE o.inventory_number = '1887,0801.61'
ON CONFLICT DO NOTHING;

-- Bronze statuette: Archaic Greek Ploughman with Team of Oxen (British Museum: 1852,0901.13)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Bronze statuette: Archaic Greek Ploughman with Team of Oxen', 'Bronze', 'Boeotia, Greece (or Asia Minor)', '1852,0901.13', 'Archaic Greek solid-cast bronze group (Cat. Bronze 180) representing an agricultural laborer guiding a two-ox team. The farmer wears a simple tunic and leans forward over a primitive ard-plow, steadying the wooden handle with both hands while driving the yoked pair of horned draft oxen through furrowed earth. Demonstrates primary tillage technology used across ancient Mediterranean farms.',
        'ca. 550–500 BCE', -550, -500, 7.5, 7.0, 21.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1852_0901_13.jpg'
FROM objects o WHERE o.inventory_number = '1852,0901.13'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1852_0901_13.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Agriculture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Agriculture'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Plowing') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Plowing'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Draft Animals') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Draft Animals'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Bronze') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Bronze'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Labor'
WHERE o.inventory_number = '1852,0901.13'
ON CONFLICT DO NOTHING;

-- Marble funerary stele: The Shoemaker Xanthippos (British Museum: 1805,0703.183)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Marble funerary stele: The Shoemaker Xanthippos', 'Pentelic marble', 'Athens, Greece', '1805,0703.183', 'Classical Athenian marble grave relief (Cat. Sculpture 628) of Xanthippos. The deceased artisan is shown as a mature bearded man seated in profile on an elegant klismos chair, with his two small daughters standing before him. In his right hand, Xanthippos proudly holds up a shoemaker''s last (kalopous), the primary carved wooden form used by cobblers and shoemakers to shape leather footwear, proudly commemorating his skilled profession.',
        'ca. 430–420 BCE', -430, -420, 83.8, 39.5, 9.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1805_0703_183.jpg'
FROM objects o WHERE o.inventory_number = '1805,0703.183'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1805_0703_183.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Shoemaking') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Shoemaking'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Artisans') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Artisans'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Funerary Relief') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Funerary Relief'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Leatherworking') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Leatherworking'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Crafts') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Crafts'
WHERE o.inventory_number = '1805,0703.183'
ON CONFLICT DO NOTHING;

-- Marble funerary relief: Freedmen Artisans Publius Licinius Philonicus & Demetrius (British Museum: 1954,1214.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Marble funerary relief: Freedmen Artisans Publius Licinius Philonicus & Demetrius', 'Luna marble', 'Near Frascati (ancient Tusculum), Lazio, Italy', '1954,1214.1', 'Marble funerary monument celebrating two Roman freedmen (liberti): Publius Licinius Philonicus and Publius Licinius Demetrius. In the central niches are realistic portrait busts of the two former slaves in Roman togas. Flanking the pediments and fascia are carved instruments of their specialized trades: at left, the blacksmith and coin minter''s anvil, tongs, and coining die hammer; at right, the carpenter and joiner''s adze, double axe, and folding measuring rule.',
        'ca. 30–10 BCE', -30, -10, 66.0, 99.0, 20.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1954_1214_1.jpg'
FROM objects o WHERE o.inventory_number = '1954,1214.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1954_1214_1.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Freedmen') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Freedmen'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Blacksmiths') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Blacksmiths'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Carpenters') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Carpenters'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Moneyers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Moneyers'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tools') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tools'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Relief') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Relief'
WHERE o.inventory_number = '1954,1214.1'
ON CONFLICT DO NOTHING;

-- Marble relief: Roman Sailor Navigating a Cargo Vessel (Corbita) (British Museum: 1850,0304.32)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Marble relief: Roman Sailor Navigating a Cargo Vessel (Corbita)', 'Marble', 'Carthage, Roman Africa Proconsularis (modern Tunisia)', '1850,0304.32', 'Roman marble architectural relief (Cat. Sculpture 2405) showing an ancient sailor maneuvering a corbita, a round-hulled Mediterranean merchant vessel used to transport olive oil amphorae, wine, and grain from North Africa to Rome. The helmsman stands at the stern gripping the steering oar (gubernaculum), managing the vessel under full sail across the waves.',
        'ca. 150–250 CE', 150, 250, 48.0, 81.0, 7.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1850_0304_32.jpg'
FROM objects o WHERE o.inventory_number = '1850,0304.32'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1850_0304_32.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Maritime') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Maritime'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Merchant Sailors') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Merchant Sailors'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Trade') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Trade'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Shipping') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Shipping'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('North Africa') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'North Africa'
WHERE o.inventory_number = '1850,0304.32'
ON CONFLICT DO NOTHING;

-- Surgical instruments: Roman Bronze Catheters and Probes (British Museum: 1968,0626.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Surgical instruments: Roman Bronze Catheters and Probes', 'Bronze', 'Italy', '1968,0626.1', 'Set of finely wrought Roman bronze surgical instruments (GR 1968.6-26.1–39), including S-shaped male catheters, curved specula, and probes. Professional Roman physicians (medici) and military camp surgeons used specialized medical kits for operations, suturing wounds, and treating bladder obstructions. Demonstrates high technical precision in Roman metalwork and medical professions.',
        'ca. 1–100 CE', 1, 100, 2.5, 5.0, 22.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1968_0626_1.jpg'
FROM objects o WHERE o.inventory_number = '1968,0626.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1968_0626_1.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Medicine') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Medicine'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Physicians') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Physicians'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Surgeons') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Surgeons'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tools') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tools'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Bronze') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Bronze'
WHERE o.inventory_number = '1968,0626.1'
ON CONFLICT DO NOTHING;

-- Vindolanda Ink Writing Tablet: Commercial Grain, Hides, and Sinews Account (Tablet 343) (British Museum: 1989,0602.74)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Vindolanda Ink Writing Tablet: Commercial Grain, Hides, and Sinews Account (Tablet 343)', 'Alder and birch wood, carbon ink', 'Vindolanda Roman Fort (Chesterholm), Northumberland, Roman Britain', '1989,0602.74', 'Wafer-thin wooden leaf tablet written in Latin cursive using carbon ink, discovered in anaerobic waterlogged soil at the Roman fort of Vindolanda near Hadrian''s Wall. Tablet 343 is a business letter from Octavius to Candidus discussing commercial deliveries: purchasing 100 modii of wheat, transporting cow hides, collecting sinew for military equipment, and financial settlements with regional traders and tanners.',
        'ca. 90–120 CE', 90, 120, 8.5, 21.0, 0.2, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1989_0602_74.jpg'
FROM objects o WHERE o.inventory_number = '1989,0602.74'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1989_0602_74.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Romano-British') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Romano-British'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Commerce') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Commerce'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Quartermasters') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Quartermasters'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Grain') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Grain'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tanning') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tanning'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Vindolanda') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Vindolanda'
WHERE o.inventory_number = '1989,0602.74'
ON CONFLICT DO NOTHING;

-- Proto-Cuneiform Clay Tablet: Daily Beer and Grain Rations for Laborers (BM 140855) (British Museum: 1989,0130.4)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Proto-Cuneiform Clay Tablet: Daily Beer and Grain Rations for Laborers (BM 140855)', 'Clay', 'Southern Mesopotamia (modern southern Iraq)', '1989,0130.4', 'One of the earliest administrative accounting documents in human history. Written in proto-cuneiform pictograms, this clay tablet records rations of barley beer and bread allotted to groups of state and temple laborers. The pictographic signs include a human head next to a triangular bowl (representing ''eating/rationing'') and a pointed conical jar (representing ''beer''). Laborers in Mesopotamia were compensated with daily grain and beer rations.',
        'ca. 3100–3000 BCE', -3100, -3000, 9.4, 6.8, 2.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1989_0130_4.jpg'
FROM objects o WHERE o.inventory_number = '1989,0130.4'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1989_0130_4.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Sumerian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Sumerian'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Beer') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Beer'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Rations') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Rations'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Labor'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Proto-Cuneiform') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Proto-Cuneiform'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Accounting') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Accounting'
WHERE o.inventory_number = '1989,0130.4'
ON CONFLICT DO NOTHING;

-- Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Hauling out of Quarry (WA 124820) (British Museum: 1851,0902.6)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Hauling out of Quarry (WA 124820)', 'Gypsum alabaster', 'Southwest Palace of Sennacherib, Court VI, Nineveh, Northern Iraq', '1851,0902.6', 'Monumental palace wall relief from Nineveh illustrating the monumental logistics of royal construction. A colossal human-headed winged bull (lamassu) weighing over 30 tons is loaded onto a massive wooden sledge in the limestone quarry at Balatai. Quarrymen and construction workers use long timber levers, wedges, and thick ropes to maneuver the sledge out of the pit, while overseers coordinate the work.',
        'ca. 700–692 BCE', -700, -692, 175.0, 210.0, 15.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1851_0902_6.jpg'
FROM objects o WHERE o.inventory_number = '1851,0902.6'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1851_0902_6.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Assyrian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Assyrian'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Quarrying') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Quarrying'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Stone Transport') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Stone Transport'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Laborers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Laborers'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Nineveh') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Nineveh'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Sennacherib') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Sennacherib'
WHERE o.inventory_number = '1851,0902.6'
ON CONFLICT DO NOTHING;

-- Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Tool-Bearers and Road Crews (WA 124821) (British Museum: 1851,0902.5)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Tool-Bearers and Road Crews (WA 124821)', 'Gypsum alabaster', 'Southwest Palace of Sennacherib, Court VI, Nineveh, Northern Iraq', '1851,0902.5', 'Panel from the Sennacherib bull-transport frieze depicting support labor work gangs preparing the path for the colossal sledge. Laborers march in organized columns carrying crosscut saws, hatchets, pickaxes, and wicker baskets piled high with gravel and earth to level hills, build ramps, and clear obstacles along the transport corridor.',
        'ca. 700–692 BCE', -700, -692, 178.0, 205.0, 15.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1851_0902_5.jpg'
FROM objects o WHERE o.inventory_number = '1851,0902.5'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1851_0902_5.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Assyrian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Assyrian'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Road Building') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Road Building'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tool Bearers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tool Bearers'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Construction') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Construction'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Nineveh') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Nineveh'
WHERE o.inventory_number = '1851,0902.5'
ON CONFLICT DO NOTHING;

-- Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Work Gangs Pulling on Sledge (WA 124822) (British Museum: 1851,0902.4)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Work Gangs Pulling on Sledge (WA 124822)', 'Gypsum alabaster', 'Southwest Palace of Sennacherib, Court VI, Nineveh, Northern Iraq', '1851,0902.4', 'Relief panel depicting hundreds of conscripted laborers and prisoners of war pulling four thick cables attached to the front of the wooden sledge carrying the colossal bull. Taskmasters armed with clubs and sticks walk alongside the lines urging the teams forward, while directors with hand trumpets signal coordinated pulling surges.',
        'ca. 700–692 BCE', -700, -692, 180.0, 215.0, 15.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1851_0902_4.jpg'
FROM objects o WHERE o.inventory_number = '1851,0902.4'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1851_0902_4.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Assyrian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Assyrian'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Hauling') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Hauling'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Conscript Labor') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Conscript Labor'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Nineveh') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Nineveh'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Construction') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Construction'
WHERE o.inventory_number = '1851,0902.4'
ON CONFLICT DO NOTHING;

-- Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Rollers and Shaduf Water-Lifters (WA 124823) (British Museum: 1851,0902.3)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Rollers and Shaduf Water-Lifters (WA 124823)', 'Gypsum alabaster', 'Southwest Palace of Sennacherib, Court VI, Nineveh, Northern Iraq', '1851,0902.3', 'Relief panel showing mechanical techniques used by Assyrian engineers to move massive stones over marshy ground. Workers lift heavy wooden rollers that have emerged behind the sledge and run them forward to place beneath the advancing runners. In the background along the riverbank, agricultural workers operate shadufs (counterweighted lever water-lifters) to irrigate fields or wet transport tracks.',
        'ca. 700–692 BCE', -700, -692, 176.0, 208.0, 15.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1851_0902_3.jpg'
FROM objects o WHERE o.inventory_number = '1851,0902.3'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1851_0902_3.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Assyrian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Assyrian'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Engineering') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Engineering'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Rollers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Rollers'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Shaduf') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Shaduf'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Irrigation') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Irrigation'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Nineveh') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Nineveh'
WHERE o.inventory_number = '1851,0902.3'
ON CONFLICT DO NOTHING;

-- Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Palace Ramp and Inscription (WA 124824) (British Museum: 1851,0902.2)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Neo-Assyrian Gypsum Relief: Transport of Winged Bull: Palace Ramp and Inscription (WA 124824)', 'Gypsum alabaster', 'Southwest Palace of Sennacherib, Court VI, Nineveh, Northern Iraq', '1851,0902.2', 'Final panel of the Nineveh bull-transport sequence showing the colossal bull arriving at the palace gates up an earthen ramp. King Sennacherib stands in his royal chariot observing the work, while master architects, scribes, and engineers supervise the placement of the monument. Inscribed above is a cuneiform text recording Sennacherib''s building achievements and the mobilization of imperial labor.',
        'ca. 700–692 BCE', -700, -692, 175.0, 195.0, 15.0, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
    object_type = EXCLUDED.object_type,
    description = EXCLUDED.description,
    material = EXCLUDED.material,
    findspot = EXCLUDED.findspot,
    date_display = EXCLUDED.date_display,
    date_start = EXCLUDED.date_start,
    date_end = EXCLUDED.date_end,
    height = EXCLUDED.height,
    width = EXCLUDED.width,
    depth = EXCLUDED.depth,
    review_status = EXCLUDED.review_status;

INSERT INTO images (object_id, source_id, image_type, view_type, file_url)
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'The British Museum. “Collection Online: Ancient Civilizations, Trades, and Labor.” London: The British Museum. https://www.britishmuseum.org/collection.'), 'Photograph', 'Front', '/api/images/bm_1851_0902_2.jpg'
FROM objects o WHERE o.inventory_number = '1851,0902.2'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id AND i.file_url = '/api/images/bm_1851_0902_2.jpg');

INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Assyrian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Assyrian'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Architecture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Architecture'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Palace Construction') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Palace Construction'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Engineers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Engineers'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Nineveh') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Nineveh'
WHERE o.inventory_number = '1851,0902.2'
ON CONFLICT DO NOTHING;

COMMIT;
