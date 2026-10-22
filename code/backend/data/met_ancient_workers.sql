-- Curated Ancient Workers from The Metropolitan Museum of Art
-- Idempotent SQL script for database population
BEGIN;

INSERT INTO sources (citation_text)
SELECT 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'
WHERE NOT EXISTS (SELECT 1 FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.');

-- Model of a Granary with Scribes (Met ID: 545281, Accession: 20.3.11)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, granary, Meketre', 'Wood, plaster, paint, linen, grain', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.11', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes. The granary shows scribes tabulating grain deliveries with reed pens on wooden tablets, while agricultural workers carry filled linen grain sacks up the staircase and dump grain into the adjoining storage silos.',
        'ca. 1981–1975 B.C.', -1981, -1981, 36.5, 56, 74.9, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.11.jpg'
FROM objects o WHERE o.inventory_number = '20.3.11'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Food') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Food'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Writing') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Writing'
WHERE o.inventory_number = '20.3.11'
ON CONFLICT DO NOTHING;

-- Model Bakery and Brewery from the Tomb of Meketre (Met ID: 544258, Accession: 20.3.12)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, Bakery, brewery, Meketre', 'Wood, gesso, paint, linen', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.12', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes. The workshop is divided into two sections: on one side, female workers grind grain with hand mills and bakers knead dough and bake loaves in conical ovens; on the other side, brewers mash sprouted grain, strain beer through sieves into fermentation jars, and seal the beer vessels.',
        'ca. 1981–1975 B.C.', -1981, -1981, 29, 55, 73, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.12.jpg'
FROM objects o WHERE o.inventory_number = '20.3.12'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.12'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.12'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.12'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.12'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '20.3.12'
ON CONFLICT DO NOTHING;

-- Model Cattle stable from the tomb of Meketre (Met ID: 544254, Accession: 20.3.9)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, Stable, Meketre, cows, cattle', 'Plastered and painted wood, gesso', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.9', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes depicting a cattle stable. Workers feed stalled cattle from mangers, while herdsmen and stable hands drive and inspect fattened spotted oxen for estate recordkeeping.',
        'ca. 1981–1975 B.C.', -1981, -1975, 28.5, 57, 72.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.9.jpg'
FROM objects o WHERE o.inventory_number = '20.3.9'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.9'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.9'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Cows') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Cows'
WHERE o.inventory_number = '20.3.9'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.9'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.9'
ON CONFLICT DO NOTHING;

-- Model of a Man Plowing (Met ID: 544255, Accession: 36.5)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, plowing, cattle, cows', 'Painted wood', 'Egypt', '36.5', 'Middle Kingdom wooden model from Lisht or Thebes depicting an ancient Egyptian agricultural worker plowing a field. The farmer grasps a wooden plow hitched to a yoked team of two oxen, holding a whip or stick to guide the draft animals.',
        'ca. 1981–1885 B.C.', -1981, -1885, 20, 19.4, 49.8, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_36.5.jpg'
FROM objects o WHERE o.inventory_number = '36.5'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '36.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '36.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '36.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ox') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ox'
WHERE o.inventory_number = '36.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '36.5'
ON CONFLICT DO NOTHING;

-- Model of a Slaughter House (Met ID: 544257, Accession: 20.3.10)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Model, Butcher, Meketre, slaughter, cows, cattle', 'Wood, paint, plaster', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.10', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes. Depicts a slaughterhouse and butchery workshop: butchers slaughter oxen on the stone pavement, catch the blood in basins, dress the carcasses, and hang long strips of meat from elevated balcony beams to cure.',
        'ca. 1981–1975 B.C.', -1981, -1975, 69.5, 58.5, 76.8, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.10.jpg'
FROM objects o WHERE o.inventory_number = '20.3.10'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Animals') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Animals'
WHERE o.inventory_number = '20.3.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.10'
ON CONFLICT DO NOTHING;

-- Model Paddling Boat (Met ID: 544211, Accession: 20.3.5)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Boat, funerary, Meketre', 'Wood, paint, plaster, linen twine, linen fabric', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.5', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes depicting an estate craft propelled by eighteen paddlers and steered by a helmsman with a steering oar, illustrating waterborne estate transportation on the Nile.',
        'ca. 1981–1975 B.C.', -1981, -1975, 53, 38, 132.5, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.5.jpg'
FROM objects o WHERE o.inventory_number = '20.3.5'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Boats') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Boats'
WHERE o.inventory_number = '20.3.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.5'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.5'
ON CONFLICT DO NOTHING;

-- Kitchen Tender being Rowed (Met ID: 544212, Accession: 20.3.3)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Boat, kitchen, Meketre;', 'Wood, paint, plaster, linen twine and cloth', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.3', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes depicting a traveling kitchen tender. While crew members row the boat, cooks prepare meals on board, grilling skewered waterfowl over a glowing charcoal brazier.',
        'ca. 1981–1975 B.C.', -1981, -1975, NULL, NULL, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.3.jpg'
FROM objects o WHERE o.inventory_number = '20.3.3'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Boats') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Boats'
WHERE o.inventory_number = '20.3.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.3'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.3'
ON CONFLICT DO NOTHING;

-- Estate Figure (Met ID: 544210, Accession: 20.3.7)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Statue, standing woman, offering; Dendur-decoded', 'Wood, gesso, paint', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.7', 'Middle Kingdom painted wooden estate figure from the Tomb of Meketre (TT 280). Depicts a female agricultural worker or estate offering bearer dressed in patterned linen, carrying a large woven basket filled with bread loaves, beer jugs, and cuts of meat on her head while clutching a live duck.',
        'ca. 1981–1975 B.C.', -1981, -1981, 112, 17, 46.7, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.7.jpg'
FROM objects o WHERE o.inventory_number = '20.3.7'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.7'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.7'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ducks') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ducks'
WHERE o.inventory_number = '20.3.7'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.7'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Women') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Women'
WHERE o.inventory_number = '20.3.7'
ON CONFLICT DO NOTHING;

-- Travelling Boat being Rowed (Met ID: 544214, Accession: 20.3.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Travelling boat, Meketre, music, harp;', 'Wood, paint, gesso, linen twine and linen fabric', 'Tomb of Meketre (TT 280, MMA 1101), Upper Egypt, Thebes, Egypt', '20.3.1', 'Middle Kingdom tomb model from the Tomb of Meketre (TT 280) at Thebes. Shows a traveling boat crewed by oarsmen rowing in unison, sailors tending the rigging, and a steersman guiding the large rudder.',
        'ca. 1981–1975 B.C.', -1981, -1981, 37, 30.5, 128, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_20.3.1.jpg'
FROM objects o WHERE o.inventory_number = '20.3.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '20.3.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '20.3.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Boats') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Boats'
WHERE o.inventory_number = '20.3.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Meketre-Models') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Meketre-Models'
WHERE o.inventory_number = '20.3.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '20.3.1'
ON CONFLICT DO NOTHING;

-- Craftsmen, Tomb of Nebamun and Ipuky (Met ID: 548568, Accession: 30.4.103)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Nebamun (TT 181), Ipuky, jewelers, carpenters, metal workers', 'Tempera on Paper', 'Upper Egypt, Thebes, Egypt', '30.4.103', 'Facsimile of a New Kingdom painted relief from the Tomb of Nebamun and Ipuky (TT 181) at Thebes. The scene documents royal craftsmen at work: jewelers stringing bead necklaces, goldsmiths weighing precious metals on balance scales and blowing blowpipes into a charcoal hearth, carpenters carving furniture, and sculptors polishing stone statues.',
        'ca. 1386–1330 BCE', -1390, -1349, 50, 159.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_30.4.103.jpg'
FROM objects o WHERE o.inventory_number = '30.4.103'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '30.4.103'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '30.4.103'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '30.4.103'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '30.4.103'
ON CONFLICT DO NOTHING;

-- Shabti of the Adoratrice of Hathor Henettawy, wife of Painedjem I (Met ID: 545947, Accession: 44.4.88)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Shabti, Queen Henettawy', 'Faience', 'First Royal Cache (TT 320), Upper Egypt, Thebes', '44.4.88', 'Brilliant blue faience shabti of Henettawy, Adoratrice of Hathor. Shabtis were funerary servant figures inscribed with Spell 6 of the Book of the Dead, magically charged to perform manual agricultural labor—plowing fields, irrigating canals, and carrying sand—on behalf of the deceased in the afterlife. The figure holds two agricultural picks and carries a seed basket over her shoulder.',
        'ca. 1080–1042 BCE', -1064, -1055, 11.7, 4.3, 2.4, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_44.4.88.jpg'
FROM objects o WHERE o.inventory_number = '44.4.88'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '44.4.88'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '44.4.88'
ON CONFLICT DO NOTHING;

-- Brickmakers, Tomb of Rekhmire (Met ID: 544649, Accession: 30.4.77)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Rekhmire (TT 100), brickmaking', 'Tempera on Paper', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '30.4.77', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes, vizier under Thutmose III. The painting documents the manufacture of mudbricks for the temple of Amun: foreign and Egyptian laborers dig alluvial mud with hoes, pour water into mud pits, pack the paste into wooden brick molds, and stack dried sun-baked bricks in uniform courses.',
        'ca. 1479–1425 BCE', -1479, -1425, 48, 68.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_30.4.77.jpg'
FROM objects o WHERE o.inventory_number = '30.4.77'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '30.4.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '30.4.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '30.4.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '30.4.77'
ON CONFLICT DO NOTHING;

-- Brickmakers Getting Water from a Pool, Tomb of Rekhmire (Met ID: 544648, Accession: 30.4.89)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Rekhmire (TT 100), pool', 'Tempera on Paper', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '30.4.89', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes. Depicts laborers drawing water in terracotta jars from a lotus-filled reservoir pool and carrying the heavy jars across their shoulders with wooden yokes to supply the brickmaking pits.',
        'ca. 1479–1425 BCE', -1479, -1425, 48.5, 45.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_30.4.89.jpg'
FROM objects o WHERE o.inventory_number = '30.4.89'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '30.4.89'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '30.4.89'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '30.4.89'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '30.4.89'
ON CONFLICT DO NOTHING;

-- Sculptors at Work, Tomb of Rekhmire (Met ID: 544655, Accession: 30.4.90)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Rekhmire (TT 100), sculptors', 'Tempera on Paper', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '30.4.90', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes. Depicts sculptors and stonemasons in the royal workshop carving, chiseling, and polishing a colossal granodiorite royal statue and sphinx using stone mallets, copper chisels, and abrasive polishers.',
        'ca. 1479–1425 BCE', -1479, -1425, 54, 38.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_30.4.90.jpg'
FROM objects o WHERE o.inventory_number = '30.4.90'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Rekhmire-Exhibition') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Rekhmire-Exhibition'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Sculpture') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Sculpture'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '30.4.90'
ON CONFLICT DO NOTHING;

-- Carpenters at Work, Tomb of Rekhmire (Met ID: 544639, Accession: 35.101.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Rekhmire (TT 100), carpenters', 'Tempera on paper', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '35.101.1', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes. Depicts royal carpenters, joiners, and woodworkers using pull-saws, bow drills, adzes, and chisels to construct ebony furniture, shrine doors, and ceremonial caskets.',
        'ca. 1479–1396 BCE', -1504, -1504, 58.5, 197, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_35.101.1.jpg'
FROM objects o WHERE o.inventory_number = '35.101.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '35.101.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '35.101.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '35.101.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Tools') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Tools'
WHERE o.inventory_number = '35.101.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '35.101.1'
ON CONFLICT DO NOTHING;

-- Metal Working, Tomb of Rekhmire (Met ID: 544647, Accession: 31.6.22)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Rekhmire (TT 100), metal work', 'Paper, tempera paint, ink', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '31.6.22', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes. Depicts metalworkers in the temple workshops smelting copper and gold: artisans use blowpipes and foot-bellows to heat crucibles over charcoal hearths, and pour molten bronze into double-handled molds to cast monumental temple gates.',
        'ca. 1479–1396 BCE', -1504, -1504, 27.5, 34.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_31.6.22.jpg'
FROM objects o WHERE o.inventory_number = '31.6.22'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '31.6.22'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '31.6.22'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '31.6.22'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Rekhmire-Exhibition') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Rekhmire-Exhibition'
WHERE o.inventory_number = '31.6.22'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '31.6.22'
ON CONFLICT DO NOTHING;

-- Scene of Metal Workers, Tomb of Rekhmire (Met ID: 544645, Accession: 31.6.11)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, metal work, bellows, Rekhmire (TT 100)', 'Tempera on paper', 'Tomb of Rekhmire (TT 100), Upper Egypt, Thebes, Egypt', '31.6.11', 'New Kingdom facsimile from the Tomb of Rekhmire (TT 100) at Thebes. Depicts goldsmiths and silversmiths hammering sheet metal, chasing delicate relief patterns on ceremonial vases, and weighing ingots on balance scales.',
        'ca. 1479–1396 BCE', -1504, -1504, 57.5, 54, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_31.6.11.jpg'
FROM objects o WHERE o.inventory_number = '31.6.11'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Egyptian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Egyptian'
WHERE o.inventory_number = '31.6.11'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '31.6.11'
ON CONFLICT DO NOTHING;

-- Sennedjem and Iineferti in the Fields of Iaru (Met ID: 548354, Accession: 30.4.2)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Facsimile, Sennedjem (TT 1), Iaru, Iinefereti, opening of the mouth, plow', 'Tempera on paper', 'Tomb of Sennedjem (TT 1)', '30.4.2', 'New Kingdom facsimile from the Tomb of Sennedjem (TT 1) at Deir el-Medina. Sennedjem, a tomb worker in the Valley of the Kings, and his wife Iineferti are depicted performing idealized agricultural labor in the Fields of Iaru (Elysian fields of the afterlife): plowing rich black soil behind a pair of yoked cattle, sowing grain seeds, and reaping tall ripe flax and emmer wheat with hand sickles.',
        '1922; original ca. 1300–1224 BCE', -1295, -1295, 54, 84.5, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_30.4.2.jpg'
FROM objects o WHERE o.inventory_number = '30.4.2'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '30.4.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Animals') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Animals'
WHERE o.inventory_number = '30.4.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Farmers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Farmers'
WHERE o.inventory_number = '30.4.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '30.4.2'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Women') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Women'
WHERE o.inventory_number = '30.4.2'
ON CONFLICT DO NOTHING;

-- Bronze statuette of an artisan with silver eyes (Met ID: 255344, Accession: 1972.11.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Statuette of an artisan, hunchback', 'Bronze, silver', 'Greek', '1972.11.1', 'Late Hellenistic bronze statuette from the 1st century BCE depicting a muscular, weathered master artisan or craftsman. He wears an exomis (short artisan tunic leaving the right shoulder bare for manual labor) and has a pair of wax writing tablets tucked into his leather belt for workshop sketches and accounts, with vivid inlaid silver eyes.',
        'ca. mid-1st century BCE', -60, -40, 40.322582, 13.017526, 10.795022, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_1972.11.1.jpg'
FROM objects o WHERE o.inventory_number = '1972.11.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '1972.11.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '1972.11.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '1972.11.1'
ON CONFLICT DO NOTHING;

-- Bronze statuette of a Black African youth (Met ID: 250673, Accession: 18.145.10)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Statuette of a black youth', 'Bronze', 'Greek', '18.145.10', 'Hellenistic bronze statuette from the 3rd–2nd century BCE depicting a young artisan or metalworker. He is clad in the standard short, working-class exomis worn by ancient Greek smiths and foundry laborers, captured in a dynamic naturalistic pose.',
        '3rd–2nd century BCE', -299, -100, 18.29, NULL, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_18.145.10.jpg'
FROM objects o WHERE o.inventory_number = '18.145.10'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '18.145.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '18.145.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Male Nudes') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Male Nudes'
WHERE o.inventory_number = '18.145.10'
ON CONFLICT DO NOTHING;

-- Terracotta lekythos (oil flask) (Met ID: 253348, Accession: 31.11.10)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Lekythos', 'Terracotta', 'Greek, Attic', '31.11.10', 'Attic black-figure lekythos (oil flask) attributed to the Amasis Painter (ca. 550–530 BCE). One of the most famous representations of ancient Greek female labor and textile production: women spin raw wool using distaffs and drop spindles, weigh wool on balance scales, weave intricate patterns on a vertical warp-weighted loom with hanging clay weights, and fold the finished cloth.',
        'ca. 550–530 BCE', -550, -530, 17.145035, 9.9, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_31.11.10.jpg'
FROM objects o WHERE o.inventory_number = '31.11.10'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '31.11.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '31.11.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Looms') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Looms'
WHERE o.inventory_number = '31.11.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Women') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Women'
WHERE o.inventory_number = '31.11.10'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Working') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Working'
WHERE o.inventory_number = '31.11.10'
ON CONFLICT DO NOTHING;

-- Terracotta hydria (water jar) (Met ID: 247244, Accession: 06.1021.77)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Hydria', 'Terracotta', 'Greek, Attic', '06.1021.77', 'Attic black-figure hydria (ca. 510–500 BCE) depicting women gathering at a civic fountain house. Female laborers and household members carry water jars (hydriai) on their heads, fill them beneath carved lion-head and panther-head waterspouts, and converse while carrying the heavy containers on shoulder cushions.',
        'ca. 510–500 BCE', -510, -500, 37.47, NULL, NULL, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_06.1021.77.jpg'
FROM objects o WHERE o.inventory_number = '06.1021.77'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Greek') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Greek'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Battles') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Battles'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Fountains') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Fountains'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Women') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Women'
WHERE o.inventory_number = '06.1021.77'
ON CONFLICT DO NOTHING;

-- Marble relief showing transport amphorae (Met ID: 251843, Accession: 25.78.63)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Relief of a wine-shop', 'Marble', 'Roman', '25.78.63', 'Roman marble relief from the 2nd century CE documenting commercial transport and trade. A merchant or warehouse manager seated with records receives a cargo delivery of sealed transport amphorae filled with wine or olive oil, carried in by a dock porter (saccarius / baiulus).',
        '2nd century CE', 100, 199, 28.257557, 42.545086, 7.620015, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_25.78.63.jpg'
FROM objects o WHERE o.inventory_number = '25.78.63'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '25.78.63'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '25.78.63'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Jars') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Jars'
WHERE o.inventory_number = '25.78.63'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '25.78.63'
ON CONFLICT DO NOTHING;

-- Terracotta oil lamp (Met ID: 241663, Accession: 74.51.2110)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Lamp', 'Terracotta', 'Roman, Cypriot', '74.51.2110', 'Roman mold-made terracotta oil lamp from Cyprus (ca. 40–100 CE). The discus depicts an enslaved domestic worker wearing a loincloth, kneeling over a large preparation basin or kneading trough, representing daily household manual labor.',
        'ca. 40–100 CE', 40, 100, 2.2225044, NULL, 8.8900175, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_74.51.2110.jpg'
FROM objects o WHERE o.inventory_number = '74.51.2110'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '74.51.2110'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '74.51.2110'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '74.51.2110'
ON CONFLICT DO NOTHING;

-- Terracotta oil lamp (Met ID: 241662, Accession: 74.51.2109)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Lamp', 'Terracotta', 'Roman, Cypriot', '74.51.2109', 'Roman mold-made terracotta oil lamp from Cyprus (ca. 40–100 CE). The discus relief depicts two enslaved laborers or porters carrying a heavy cargo amphora slung from a shoulder pole, illustrating commercial portage.',
        'ca. 40–100 CE', 40, 100, 2.540005, NULL, 9.207519, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_74.51.2109.jpg'
FROM objects o WHERE o.inventory_number = '74.51.2109'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Roman') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Roman'
WHERE o.inventory_number = '74.51.2109'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '74.51.2109'
ON CONFLICT DO NOTHING;

-- Foundation figure of Ur-Namma holding a basket (Met ID: 329067, Accession: 47.49)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Foundation figure', 'Copper alloy', 'Mesopotamia', '47.49', 'Neo-Sumerian copper alloy foundation peg (ca. 2112–2095 BCE) from Nippur or Ur. Depicts King Ur-Namma assuming the persona of the master builder, carrying a builder’s basket filled with clay mortar on his head to lay the first brick of the temple of Enlil.',
        'ca. 2112–2095 BCE', -2112, -2095, 27.3, 9.1, 5.6, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_47.49.jpg'
FROM objects o WHERE o.inventory_number = '47.49'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '47.49'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '47.49'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Men') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Men'
WHERE o.inventory_number = '47.49'
ON CONFLICT DO NOTHING;

-- Foundation figure of king Shulgi of Ur, carrying a basket (Met ID: 324831, Accession: 59.41.1)
INSERT INTO objects (object_type, material, findspot, inventory_number, description,
                     date_display, date_start, date_end, height, width, depth, unit, review_status)
VALUES ('Foundation figure', 'Copper', 'Mesopotamia', '59.41.1', 'Neo-Sumerian copper foundation figure (ca. 2094–2047 BCE) from Nippur. Depicts King Shulgi of Ur carrying a builder’s basket of earth and brick mortar on his head for the sacred foundation ceremony of the temple of Inanna.',
        'ca. 2094–2047 BCE', -2094, -2047, 31.09, 8.8, 5.6, 'cm', 'accepted')
ON CONFLICT (inventory_number) DO UPDATE SET
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
SELECT o.id, (SELECT id FROM sources WHERE citation_text = 'Metropolitan Museum of Art. “The Met Collection: Ancient Civilizations and Labor.” New York: The Metropolitan Museum of Art. https://www.metmuseum.org/art/collection.'), 'Photograph', 'Front', '/api/images/met_59.41.1.jpg'
FROM objects o WHERE o.inventory_number = '59.41.1'
  AND NOT EXISTS (SELECT 1 FROM images i WHERE i.object_id = o.id);
INSERT INTO tags (tag_name) VALUES ('Ancient Mesopotamian') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Mesopotamian'
WHERE o.inventory_number = '59.41.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Ancient Workers') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Ancient Workers'
WHERE o.inventory_number = '59.41.1'
ON CONFLICT DO NOTHING;
INSERT INTO tags (tag_name) VALUES ('Kings') ON CONFLICT (tag_name) DO NOTHING;
INSERT INTO image_tags (image_id, tag_id)
SELECT i.id, t.id FROM images i
JOIN objects o ON o.id = i.object_id
JOIN tags t ON t.tag_name = 'Kings'
WHERE o.inventory_number = '59.41.1'
ON CONFLICT DO NOTHING;

COMMIT;