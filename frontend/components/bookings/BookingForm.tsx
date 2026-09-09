"use client";

import { useState } from "react";

export default function BookingForm() {
  const [jobRequirementId, setJobRequirementId] = useState("");
  const [workersNeeded, setWorkersNeeded] = useState("1");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    console.log({
      job_requirement_id: jobRequirementId,
      workers_needed: Number(workersNeeded),
      start_time: startTime,
      end_time: endTime,
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="mb-2 block text-sm font-medium">
          Job Requirement ID
        </label>
        <input
          value={jobRequirementId}
          onChange={(event) => setJobRequirementId(event.target.value)}
          placeholder="Enter job requirement ID"
          className="w-full rounded-lg border px-4 py-2"
          required
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium">
          Workers Needed
        </label>
        <input
          type="number"
          min="1"
          value={workersNeeded}
          onChange={(event) => setWorkersNeeded(event.target.value)}
          className="w-full rounded-lg border px-4 py-2"
          required
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium">
          Start Time
        </label>
        <input
          type="datetime-local"
          value={startTime}
          onChange={(event) => setStartTime(event.target.value)}
          className="w-full rounded-lg border px-4 py-2"
          required
        />
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium">
          End Time
        </label>
        <input
          type="datetime-local"
          value={endTime}
          onChange={(event) => setEndTime(event.target.value)}
          className="w-full rounded-lg border px-4 py-2"
          required
        />
      </div>

      <button
        type="submit"
        className="rounded-lg border px-5 py-2.5 text-sm font-medium"
      >
        Create Booking
      </button>
    </form>
  );
}