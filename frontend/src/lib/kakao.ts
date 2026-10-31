// Store search with the Kakao Maps SDK (services library). It runs in the browser, so it uses the
// JavaScript key, which Kakao only accepts from the site domains registered on the app.
import { DISTRICT_NAMES } from "@/lib/districts";
import type { NewStore, StoreCategory } from "@/lib/reviews";

type KakaoPlace = {
  place_name: string;
  address_name: string;
  road_address_name: string;
  category_group_code: string;
  category_name: string;
};

type Places = {
  keywordSearch: (query: string, callback: (data: KakaoPlace[], status: string) => void, options: { size: number }) => void;
};

declare global {
  interface Window {
    kakao: { maps: { load: (callback: () => void) => void; services: { Places: new () => Places } } };
  }
}

const KEY = process.env.NEXT_PUBLIC_KAKAO_JS_KEY;
const SDK_URL = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KEY}&libraries=services&autoload=false`;

const CATEGORY_BY_GROUP: Record<string, StoreCategory> = {
  FD6: "restaurant",
  CE7: "cafe",
  CS2: "convenience",
  MT1: "market",
};

let places: Promise<Places> | null = null;

function loadPlaces(): Promise<Places> {
  places ??= new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SDK_URL;
    script.onload = () => window.kakao.maps.load(() => resolve(new window.kakao.maps.services.Places()));
    script.onerror = () => {
      places = null; // try again on the next search
      reject(new Error("Kakao SDK failed to load"));
    };
    document.head.appendChild(script);
  });
  return places;
}

/** Kakao files bars under restaurants (FD6), so they are told apart by the category text. */
function categoryOf(place: KakaoPlace): StoreCategory {
  if (place.category_name.includes("술집")) return "bar";
  return CATEGORY_BY_GROUP[place.category_group_code] ?? "other";
}

/** Returns null outside Seoul: reviews are tagged with one of Seoul's 25 districts. */
function toNewStore(place: KakaoPlace): NewStore | null {
  const [city, district] = place.address_name.split(" ");
  if (!city?.startsWith("서울")) return null;
  return {
    name: place.place_name,
    category: categoryOf(place),
    district: DISTRICT_NAMES.includes(district) ? district : null,
    address: place.road_address_name || place.address_name,
  };
}

/** Seoul places matching the keyword. Any failure gives no results, so manual entry still works. */
export async function searchKakaoPlaces(query: string): Promise<NewStore[]> {
  if (!KEY) return [];
  const service = await loadPlaces();
  return new Promise((resolve) => {
    service.keywordSearch(
      `서울 ${query}`,
      (data, status) => resolve(status === "OK" ? data.map(toNewStore).filter((s) => s !== null) : []),
      { size: 8 },
    );
  });
}
