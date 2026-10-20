import React from "react";
import { DaiNoiClient } from "./DaiNoiClient";
import { fetchActiveMap, fetchSites, fetchZones } from "@/lib/imperial/map-api";

export const revalidate = 60; // 1 minute ISR cache

export default async function DaiNoiPage() {
  const [activeMap, zones, sites] = await Promise.all([
    fetchActiveMap(),
    fetchZones(),
    fetchSites(),
  ]);

  return (
    <DaiNoiClient
      initialActiveMap={activeMap}
      initialZones={zones}
      initialSites={sites}
      fullscreen={false}
    />
  );
}
