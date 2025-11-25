import { useMemo, useState } from "react";
import {
  Autocomplete,
  Chip,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";

export type FilterValue = "ALL" | string;

export type Member = {
  id: string;
  displayName: string;
  branch: string;
  status: string;
  generations: string[];
  searchKeywords: string[];
};

export type MemberMultiSelectProps = {
  members: Member[];
  value: string[];
  onChange: (ids: string[]) => void;
  initialTextQuery?: string;
  initialBranchFilter?: FilterValue;
  initialStatusFilter?: FilterValue;
  initialGenerationFilter?: FilterValue;
};

/**
 * Member selector with tag-style chips, branch/status/generation filters,
 * and search over member search keywords.
 */
export function MemberMultiSelect({
  members,
  value,
  onChange,
  initialTextQuery = "",
  initialBranchFilter = "ALL",
  initialStatusFilter = "ALL",
  initialGenerationFilter = "ALL",
}: MemberMultiSelectProps) {
  const [textQuery, setTextQuery] = useState(initialTextQuery);
  const [branchFilter, setBranchFilter] = useState<FilterValue>(initialBranchFilter);
  const [statusFilter, setStatusFilter] = useState<FilterValue>(initialStatusFilter);
  const [generationFilter, setGenerationFilter] = useState<FilterValue>(
    initialGenerationFilter,
  );

  const optionById = useMemo(() => {
    const map = new Map<string, Member>();
    members.forEach((member) => map.set(member.id, member));
    return map;
  }, [members]);

  const selectedMembers = useMemo(
    () => value.map((id) => optionById.get(id)).filter(Boolean) as Member[],
    [optionById, value],
  );

  const branchOptions = useMemo(
    () => ["ALL", ...Array.from(new Set(members.map((m) => m.branch).filter(Boolean))).sort()],
    [members],
  );
  const statusOptions = useMemo(
    () => ["ALL", ...Array.from(new Set(members.map((m) => m.status).filter(Boolean))).sort()],
    [members],
  );
  const generationOptions = useMemo(
    () => [
      "ALL",
      ...Array.from(new Set(members.flatMap((m) => m.generations || []).filter(Boolean))).sort(),
    ],
    [members],
  );

  const filteredMembers = useMemo(() => {
    const query = textQuery.trim().toLowerCase();
    const matchesQuery = (member: Member) => {
      if (!query) return true;
      const keywords = [...member.searchKeywords, member.displayName].map((kw) =>
        kw.toLowerCase(),
      );
      return keywords.some((kw) => kw.includes(query));
    };

    const matchesBranch = (member: Member) =>
      branchFilter === "ALL" || member.branch === branchFilter;
    const matchesStatus = (member: Member) =>
      statusFilter === "ALL" || member.status === statusFilter;
    const matchesGeneration = (member: Member) =>
      generationFilter === "ALL" || (member.generations || []).includes(generationFilter);

    const selected = new Set(value);

    return members.filter(
      (member) =>
        !selected.has(member.id) &&
        matchesBranch(member) &&
        matchesStatus(member) &&
        matchesGeneration(member) &&
        matchesQuery(member),
    );
  }, [branchFilter, generationFilter, members, statusFilter, textQuery, value]);

  return (
    <Stack spacing={2} sx={{ minWidth: 320 }}>
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          select
          fullWidth
          label="Branch"
          value={branchFilter}
          onChange={(event) => setBranchFilter(event.target.value as FilterValue)}
        >
          {branchOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option === "ALL" ? "All branches" : option}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          fullWidth
          label="Status"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value as FilterValue)}
        >
          {statusOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option === "ALL" ? "All statuses" : option}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          fullWidth
          label="Generation"
          value={generationFilter}
          onChange={(event) => setGenerationFilter(event.target.value as FilterValue)}
        >
          {generationOptions.map((option) => (
            <MenuItem key={option} value={option}>
              {option === "ALL" ? "All generations" : option}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      <Autocomplete
        multiple
        disableCloseOnSelect
        options={filteredMembers}
        value={selectedMembers}
        getOptionLabel={(option) => option.displayName}
        inputValue={textQuery}
        onInputChange={(_, newValue) => setTextQuery(newValue)}
        onChange={(_, newValue) => onChange(newValue.map((member) => member.id))}
        renderTags={(tagValue, getTagProps) =>
          tagValue.map((option, index) => (
            <Chip
              {...getTagProps({ index })}
              key={option.id}
              label={option.displayName}
              sx={{ mr: 0.5 }}
            />
          ))
        }
        renderOption={(props, option) => (
          <li {...props} key={option.id}>
            <Stack spacing={0.25}>
              <Typography variant="body1">{option.displayName}</Typography>
              <Typography variant="caption" color="text.secondary">
                {[option.branch, option.status, (option.generations || []).join(", ")]
                  .filter(Boolean)
                  .join(" · ") || "No metadata"}
              </Typography>
            </Stack>
          </li>
        )}
        renderInput={(params) => (
          <TextField
            {...params}
            label="Members"
            placeholder="メンバーを検索"
            helperText="タグ入力＋Backspaceで直前のタグ削除が可能"
          />
        )}
      />
    </Stack>
  );
}

export default MemberMultiSelect;
