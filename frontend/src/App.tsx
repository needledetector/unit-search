import { useMemo, useState } from "react";
import { CssBaseline, Container, Paper, Stack, Typography } from "@mui/material";
import MemberMultiSelect, { Member } from "./MemberMultiSelect";

const sampleMembers: Member[] = [
  {
    id: "m1",
    displayName: "山田 太郎",
    branch: "JP",
    status: "active",
    generations: ["1st"],
    searchKeywords: ["Taro", "Yamada", "やまだ", "たろう"],
  },
  {
    id: "m2",
    displayName: "Jane Doe",
    branch: "EN",
    status: "active",
    generations: ["0th"],
    searchKeywords: ["Jane", "Doe"],
  },
  {
    id: "m3",
    displayName: "李 小龍",
    branch: "HK",
    status: "graduated",
    generations: ["2nd"],
    searchKeywords: ["Bruce", "Lee", "イー・シャオロン"],
  },
  {
    id: "m4",
    displayName: "鈴木 花子",
    branch: "JP",
    status: "active",
    generations: ["2nd"],
    searchKeywords: ["Hanako", "Suzuki"],
  },
];

function App() {
  const [selectedMemberIds, setSelectedMemberIds] = useState<string[]>(["m1"]);

  const selectedLabels = useMemo(() => {
    const map = new Map(sampleMembers.map((member) => [member.id, member.displayName]));
    return selectedMemberIds.map((id) => map.get(id) ?? id);
  }, [selectedMemberIds]);

  return (
    <>
      <CssBaseline />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          MemberMultiSelect デモ
        </Typography>
        <Typography variant="body1" color="text.secondary" gutterBottom>
          フィルターとキーワード検索を組み合わせて候補を絞り込んだ上で、複数のメンバーをタグ入力で選択できるデモです。
        </Typography>

        <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
          <MemberMultiSelect
            members={sampleMembers}
            value={selectedMemberIds}
            onChange={setSelectedMemberIds}
          />
        </Paper>

        <Stack spacing={0.5} sx={{ mt: 3 }}>
          <Typography variant="subtitle1">選択中のメンバー:</Typography>
          {selectedLabels.length ? (
            selectedLabels.map((name) => (
              <Typography key={name} variant="body2">
                • {name}
              </Typography>
            ))
          ) : (
            <Typography variant="body2" color="text.secondary">
              まだ選択されていません。
            </Typography>
          )}
        </Stack>
      </Container>
    </>
  );
}

export default App;
