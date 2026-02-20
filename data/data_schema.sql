PRAGMA foreign_keys = ON;

CREATE TABLE "reviews" (
  "review_id" TEXT PRIMARY KEY,
  "title" TEXT,
  "text" TEXT,
  "date_stayed" TIMESTAMP,
  "num_helpful_votes" INTEGER,
  "review_date" TIMESTAMP,
  "via_mobile" INTEGER,
  "service_rating" REAL,
  "cleanliness_rating" REAL,
  "overall_rating" REAL,
  "value_rating" REAL,
  "location_rating" REAL,
  "sleep_quality_rating" REAL,
  "rooms_rating" REAL,
  "check_in_service_rating" REAL,
  "business_service_rating" REAL,
  "hotel_id" TEXT,
  "author_id" TEXT,

  FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id),
  FOREIGN KEY (author_id) REFERENCES authors(id )
);

CREATE TABLE "authors" (
  "id" TEXT PRIMARY KEY,
  "username" TEXT,
  "num_cities" REAL,
  "num_helpful_votes" REAL,
  "num_reviews" REAL,
  "num_type_reviews" REAL,
  "location" TEXT,
  "alias" TEXT
);

CREATE TABLE "hotels" (
  "hotel_id" TEXT PRIMARY KEY,
  "num_reviews" INTEGER,
  "avg_service_rating" REAL,
  "avg_cleanliness_rating" REAL,
  "avg_overall_rating" REAL,
  "avg_value_rating" REAL,
  "avg_location_rating" REAL,
  "avg_sleep_quality_rating" REAL,
  "avg_rooms_rating" REAL,
  "avg_check_in_service_rating" REAL,
  "avg_business_service_rating" REAL
);


CREATE INDEX idx_authors_id ON authors(id);

CREATE INDEX idx_hotels_hotel_id ON hotels(hotel_id);

CREATE INDEX idx_reviews_date ON reviews(review_date);

CREATE INDEX idx_reviews_hotel ON reviews(hotel_id);

CREATE INDEX idx_reviews_hotel_date ON reviews(hotel_id, review_date);

CREATE UNIQUE INDEX ux_authors_id ON authors(id);

CREATE UNIQUE INDEX ux_hotels_hotel_id ON hotels(hotel_id);

CREATE UNIQUE INDEX ux_reviews_review_id ON reviews(review_id);
