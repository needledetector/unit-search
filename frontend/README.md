# React UI prototype

`frontend/src/MemberMultiSelect.tsx` provides a Material UI-based member selector that matches the desired behavior:

- **Tag-style multi-select:** Uses `Autocomplete` with chips; backspace removes the preceding tag using MUI defaults.
- **Dynamic filters:** Branch, status, and generation dropdowns narrow the candidate list before suggestion rendering.
- **Searchable keywords:** The text query performs a substring match against `searchKeywords` plus `displayName`, ignoring already-selected IDs.

## Usage

```tsx
import MemberMultiSelect, { Member } from "./MemberMultiSelect";

const members: Member[] = [
  {
    id: "m1",
    displayName: "Example Member",
    branch: "JP",
    status: "active",
    generations: ["1st"],
    searchKeywords: ["Example", "エグザンプル"],
  },
  // ...
];

function Example() {
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>([]);

  return (
    <MemberMultiSelect
      members={members}
      value={selectedMemberIds}
      onChange={setSelectedMemberIds}
    />
  );
}
```

The component is hook-driven and does not assume any global state container, so it can slot into an existing React or Next.js page with MUI installed.

## Local demo (Vite)

A minimal Vite + React + TypeScript setup is included so you can try the component immediately.

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Start the dev server:
   ```bash
   npm run dev -- --host
   ```
3. Open the printed local URL (default http://localhost:5173/). The page renders `MemberMultiSelect` with sample data and shows the currently selected names.

The demo code lives in `src/App.tsx` and uses the same exported component from `src/MemberMultiSelect.tsx`, so you can adapt it as a starting point for your app.
