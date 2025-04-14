CREATE TYPE room_type AS ENUM ('Emergency', 'ICU', 'Ward', 'Normal');
CREATE TYPE comm_type AS ENUM ('Phone','Email');

DROP TABLE IF EXISTS patient_info;
CREATE TABLE patient_info (
    patient_id BIGSERIAL PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
	prefered_communication comm_type DEFAULT 'Email',
    gender VARCHAR(10),
	symptoms TEXT,
	symptoms_duration VARCHAR(20),
	treatment TEXT DEFAULT NULL,
    vitals JSONB,
	treatment_completed BOOLEAN DEFAULT FALSE,
	treatment_completion_time TIMESTAMP,
	visit_datetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS rooms;
CREATE TABLE rooms (
    room_number INT PRIMARY KEY,
    type room_type NOT NULL,
    is_occupied BOOLEAN DEFAULT FALSE
);

DROP TABLE IF EXISTS doctors;
CREATE TABLE doctors (
    doctor_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialist VARCHAR(100),
	is_busy BOOLEAN DEFAULT FALSE,
    busy_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    busy_till TIMESTAMP
);

DROP TABLE IF EXISTS ongoing_cases;
CREATE TABLE ongoing_cases (
    patient_id INT REFERENCES patient_info(patient_id),
	doctor_id INT REFERENCES doctors(doctor_id),
    room_number INT REFERENCES rooms(room_number)
);

DROP TABLE IF EXISTS queue;
CREATE TABLE queue (
	patient_id INT REFERENCES patient_info(patient_id),
	priority_score NUMERIC,
	type_of_room room_type 
);

CREATE OR REPLACE FUNCTION release_room_and_doctor_status()
RETURNS TRIGGER AS
	$$
	BEGIN
		UPDATE rooms SET is_occupied = FALSE WHERE room_number = OLD.room_number;
		UPDATE doctors SET is_busy = FALSE WHERE doctor_id = OLD.doctor_id;
		RETURN OLD;
	END;
	$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER release_case_trigger
	BEFORE DELETE ON ongoing_cases
	FOR EACH ROW
	EXECUTE FUNCTION release_room_and_doctor_status();

CREATE OR REPLACE FUNCTION refresh_data()
RETURNS void AS
	$$
	BEGIN
		UPDATE doctors SET is_busy = FALSE,busy_till=NULL,busy_from=NULL WHERE busy_till < CURRENT_TIMESTAMP;
		
		UPDATE ongoing_cases SET doctor_id = NULL
		WHERE doctor_id IN (
			SELECT doctor_id FROM doctors WHERE is_busy=FALSE
		);
		
		UPDATE rooms SET is_occupied = FALSE
		WHERE room_number IN (
			SELECT room_number FROM rooms
			EXCEPT
			SELECT DISTINCT room_number FROM ongoing_cases
		);
	END;
	$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_available_doctors(spclty VARCHAR)
	RETURNS SETOF doctors AS
	$$
	BEGIN
		-- SELECT refresh_data();
		RETURN QUERY SELECT * FROM doctors WHERE specialist = spclty AND is_busy = FALSE;
	END;
	$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_available_rooms(ctgry room_type)
	RETURNS SETOF rooms AS
	$$
	BEGIN
		RETURN QUERY SELECT * FROM rooms WHERE rooms.type = ctgry AND is_occupied = FALSE;
	END;
	$$ LANGUAGE plpgsql;