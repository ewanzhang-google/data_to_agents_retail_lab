/*##################################################################################
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
###################################################################################*/

/*
CREATE RESERVATION `data-analytics-preview.region-us.continuous-query-reservation`
OPTIONS (
  edition = "enterprise",
  slot_capacity = 100);


CREATE ASSIGNMENT `data-analytics-preview.region-us.continuous-query-reservation.continuous-query-reservation-assignment`
OPTIONS(
   assignee = "projects/data-analytics-preview",
   job_type = "CONTINUOUS");  

DROP ASSIGNMENT `data-analytics-preview.region-us.continuous-query-reservation.continuous-query-reservation-assignment`;
DROP RESERVATION `data-analytics-preview.region-us.continuous-query-reservation`;

-- Create Service Account
-- Grant BQ access
-- Grant access to dataset
-- Grant access to Pub/Sub

EXPORT DATA OPTIONS(uri="https://pubsub.googleapis.com/projects/data-analytics-preview/topics/bq-continuous-query", format="cloud_pubsub") AS 
SELECT TO_JSON_STRING(STRUCT(customer_id,
                             current_latitude,
                             current_longitude,
                             debug_map_url)) AS message,
      TO_JSON(STRUCT(CAST(TIMESTAMP_MILLIS(event_timestamp_millis) AS STRING) AS event_timestamp)) AS _ATTRIBUTES
FROM `data-analytics-preview.chocolate_ai.customer_geo_location`;

kafka-continuous-query@data-analytics-preview.iam.gserviceaccount.com
*/

/*
EXPORT DATA OPTIONS(uri="https://pubsub.googleapis.com/projects/data-analytics-preview/topics/bq-continuous-query", format="cloud_pubsub") AS 
SELECT TO_JSON_STRING(STRUCT(customer_id,
                             current_latitude,
                             current_longitude,
                             debug_map_url)) AS message,
      TO_JSON(STRUCT(CAST(TIMESTAMP_MILLIS(event_timestamp_millis) AS STRING) AS event_timestamp)) AS _ATTRIBUTES
FROM `data-analytics-preview.chocolate_ai.customer_geo_location`;
*/


EXPORT DATA OPTIONS(uri="https://pubsub.googleapis.com/projects/data-analytics-preview/topics/bq-continuous-query", format="cloud_pubsub") AS 
WITH raw_data AS (
  SELECT *
  FROM `data-analytics-preview.chocolate_ai.customer_geo_location`
)
, geo_data AS (
  SELECT *,
         ST_DISTANCE(
          ST_GEOGPOINT(prior_longitude, prior_latitude),
          ST_GEOGPOINT(current_longitude, current_latitude)
         ) AS meters_travel_since_prior_distance,
         ST_DISTANCE(
          ST_GEOGPOINT(current_longitude, current_latitude),
          ST_GEOGPOINT(debug_destination_longitude, debug_destination_latitude)
         ) AS meters_to_dest_distance,
         ST_DISTANCE(
          ST_GEOGPOINT(current_longitude, current_latitude),
          ST_GEOGPOINT(debug_destination_longitude, debug_destination_latitude)
         ) / 1000 AS km_to_dest_distance,
  FROM raw_data
)
, results AS (
  SELECT *,
         CASE WHEN meters_to_dest_distance > 1000
               AND meters_to_dest_distance - meters_travel_since_prior_distance < 1000
              THEN TRUE
              ELSE FALSE
          END AS entered_geofence
  FROM geo_data
)
SELECT TO_JSON_STRING(STRUCT(customer_geo_location_id,
                             customer_id,
                             current_latitude,
                             current_longitude,
                             km_to_dest_distance,
                             debug_map_url)) AS message,
      TO_JSON(STRUCT(CAST(TIMESTAMP_MILLIS(event_timestamp_millis) AS STRING) AS event_timestamp)) AS _ATTRIBUTES
  FROM results
  where entered_geofence = true;
