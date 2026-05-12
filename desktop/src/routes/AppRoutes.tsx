import { Navigate, Route, createHashRouter, createRoutesFromElements } from "react-router-dom";

import { AppShell } from "../components/AppShell";
import { CalendarPage } from "../features/calendar/CalendarPage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { EditorialProfilePage } from "../features/editorial/EditorialProfilePage";
import { EventDetailPage } from "../features/events/EventDetailPage";
import { EventsPage } from "../features/events/EventsPage";
import { LibraryPage } from "../features/library/LibraryPage";
import { PiecesPage } from "../features/pieces/PiecesPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { VisualStylesPage } from "../features/visualStyles/VisualStylesPage";

export const router = createHashRouter(
  createRoutesFromElements(
    <Route element={<AppShell />}>
      <Route index element={<DashboardPage />} />
      <Route path="events" element={<EventsPage />} />
      <Route path="events/:eventId" element={<EventDetailPage />} />
      <Route path="library" element={<LibraryPage />} />
      <Route path="pieces" element={<PiecesPage />} />
      <Route path="calendar" element={<CalendarPage />} />
      <Route
        path="editorial-profile"
        element={<EditorialProfilePage />}
      />
      <Route path="visual-styles" element={<VisualStylesPage />} />
      <Route
        path="settings"
        element={<SettingsPage />}
      />
      <Route path="*" element={<Navigate replace to="/" />} />
    </Route>
  )
);
