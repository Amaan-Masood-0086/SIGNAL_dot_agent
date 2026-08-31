"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Controller, useForm, useWatch } from "react-hook-form";

import { Badge } from "@/src/components/ui/Badge";
import { Button } from "@/src/components/ui/Button";
import { Card, CardBody, CardTitle } from "@/src/components/ui/Card";
import { Input } from "@/src/components/ui/Input";
import {
  childCreateSchema,
  type ChildCreateInput,
} from "@/src/lib/api/schemas";

interface SuccessState {
  id: string;
  name: string;
  dob_confirmed: boolean;
}

async function submitIntake(input: ChildCreateInput): Promise<SuccessState> {
  const response = await fetch("/api/children", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  const body = (await response.json().catch(() => null)) as {
    child?: SuccessState;
    detail?: string;
  } | null;
  if (!response.ok || !body?.child) {
    throw new Error(body?.detail ?? "Intake failed");
  }
  return body.child;
}

// FEAT-02 acceptance: the UI clearly distinguishes the two age-entry modes
// (ADR-02). The selection is a real choice, never a silent default.
export function ChildIntakeForm() {
  const [success, setSuccess] = useState<SuccessState | null>(null);

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChildCreateInput>({
    resolver: zodResolver(childCreateSchema),
    defaultValues: {
      name: "",
      dob_confirmed: true,
      dob: "",
      estimated_age_range: "",
      estimated_age_note: "",
    },
  });
  // useWatch (not form.watch) — the compiler-safe subscription API.
  const dobConfirmed = useWatch({ control, name: "dob_confirmed" });

  const mutation = useMutation({
    mutationFn: submitIntake,
    onSuccess: (child) => {
      setSuccess(child);
      reset();
    },
  });

  if (success) {
    return (
      <Card>
        <CardTitle>Registration complete</CardTitle>
        <CardBody>
          <p className="text-sm text-ink">
            <strong>{success.name}</strong> has been registered.
          </p>
          <div className="mt-2">
            <Badge tone={success.dob_confirmed ? "success" : "warning"}>
              {success.dob_confirmed ? "Confirmed date of birth" : "Estimated age"}
            </Badge>
          </div>
          <div className="mt-4 flex gap-3">
            <Link href={`/dashboard/children/${success.id}`}>
              <Button aria-label="View child profile">View profile</Button>
            </Link>
            <Button variant="secondary" onClick={() => setSuccess(null)}>
              Register another child
            </Button>
          </div>
        </CardBody>
      </Card>
    );
  }

  return (
    <Card>
      <CardTitle>Register a child</CardTitle>
      <CardBody>
        <form
          onSubmit={handleSubmit((values) => {
            // ADR-02: send exactly one representation, never both.
            const input: ChildCreateInput = values.dob_confirmed
              ? {
                  name: values.name,
                  dob_confirmed: true,
                  dob: values.dob,
                  estimated_age_range: null,
                  estimated_age_note: null,
                }
              : {
                  name: values.name,
                  dob_confirmed: false,
                  dob: null,
                  estimated_age_range: values.estimated_age_range,
                  estimated_age_note: values.estimated_age_note || null,
                };
            mutation.mutate(input);
          })}
          className="flex flex-col gap-5"
          noValidate
        >
          <Input
            id="child-name"
            label="Child name or identifier"
            autoComplete="off"
            error={errors.name?.message}
            {...register("name")}
          />

          {/* The two entry modes — visually and semantically distinct. */}
          <fieldset className="flex flex-col gap-2">
            <legend className="text-sm font-medium text-ink-soft">
              Date of birth status
            </legend>
            <Controller
              control={control}
              name="dob_confirmed"
              render={({ field }) => (
                <div className="grid gap-3 sm:grid-cols-2">
                  <label
                    className={`flex cursor-pointer flex-col gap-1 rounded-lg border p-4 transition-colors duration-150 ${
                      field.value === true
                        ? "border-pine bg-moss ring-1 ring-pine"
                        : "border-line bg-surface hover:border-pine/50"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="dob-mode"
                        checked={field.value === true}
                        onChange={() => field.onChange(true)}
                        aria-label="Date of birth is confirmed"
                        className="accent-pine"
                      />
                      <span className="text-sm font-semibold text-ink">
                        Date of birth is confirmed
                      </span>
                    </span>
                    <span className="text-xs text-ink-soft">
                      Documentation exists (e.g. birth record or intake file).
                    </span>
                  </label>
                  <label
                    className={`flex cursor-pointer flex-col gap-1 rounded-lg border p-4 transition-colors duration-150 ${
                      field.value === false
                        ? "border-amber bg-amber-soft ring-1 ring-amber"
                        : "border-line bg-surface hover:border-pine/50"
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="dob-mode"
                        checked={field.value === false}
                        onChange={() => field.onChange(false)}
                        aria-label="Age is estimated — no confirmed date of birth"
                        className="accent-pine"
                      />
                      <span className="text-sm font-semibold text-ink">
                        Age is estimated (no confirmed DOB)
                      </span>
                    </span>
                    <span className="text-xs text-ink-soft">
                      No documentation — enter an age range instead. Flags are
                      confidence-downgraded automatically.
                    </span>
                  </label>
                </div>
              )}
            />
            {errors.dob_confirmed?.message && (
              <p role="alert" className="text-xs font-medium text-red">
                {errors.dob_confirmed.message}
              </p>
            )}
          </fieldset>

          {dobConfirmed ? (
            <Input
              id="child-dob"
              label="Confirmed date of birth"
              type="date"
              error={errors.dob?.message}
              {...register("dob")}
            />
          ) : (
            <>
              <Input
                id="child-age-range"
                label="Estimated age range"
                placeholder="e.g. 30-36 months"
                hint="Your best estimate in months."
                error={errors.estimated_age_range?.message}
                {...register("estimated_age_range")}
              />
              <div className="flex flex-col gap-1">
                <label
                  htmlFor="child-age-note"
                  className="text-sm font-medium text-ink-soft"
                >
                  How was the age estimated? (optional)
                </label>
                <textarea
                  id="child-age-note"
                  rows={2}
                  className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-soft/60 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-pine"
                  aria-describedby="child-age-note-hint"
                  {...register("estimated_age_note")}
                />
                <p id="child-age-note-hint" className="text-xs text-ink-soft">
                  e.g. &ldquo;intake worker estimate&rdquo;.
                </p>
              </div>
            </>
          )}

          {mutation.isError && (
            <p role="alert" className="rounded-lg bg-red-soft p-3 text-sm font-medium text-red">
              {mutation.error instanceof Error
                ? mutation.error.message
                : "Intake failed"}
            </p>
          )}

          <div>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? "Saving…" : "Register child"}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
