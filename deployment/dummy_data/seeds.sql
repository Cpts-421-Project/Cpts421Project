-- Insert Dummy Data

-- Sources
INSERT INTO sources (citation_text) VALUES 
('Museum of Antiquities, Collection 2024'),
('Private Collection of J. Doe');

-- Objects
INSERT INTO objects (object_type, material, findspot, latitude, longitude, date_discovered, inventory_number, date_display, date_start, date_end, width, height, depth) VALUES
('Athenian Vase', 'Clay', 'Athens, Greece', 37.9838, 23.7275, '1920-05-15', 'ATH-2024-001', 'c. 450 BC', -450, -440, 30.5, 45.0, 30.5),
('Roman Coin', 'Silver', 'Rome, Italy', 41.9028, 12.4964, '1985-11-20', 'ROM-1985-055', 'c. 100 AD', 100, 110, 2.5, 2.5, 0.2);

-- Images
-- Note: File URLs point to the local MinIO instance accessible via localhost (for browser) or minio container (internal)
-- Using localhost:9000 for browser-accessible URLs in this context
INSERT INTO images (object_id, source_id, image_type, view_type, file_url) VALUES
(1, 1, 'Photograph', 'Front', 'http://localhost:9000/uploads/vase.png'),
(2, 2, 'Photograph', 'Obverse', 'http://localhost:9000/uploads/coin.png');
