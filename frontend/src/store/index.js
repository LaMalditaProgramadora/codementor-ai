import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  user: null,
  role: localStorage.getItem('userRole') || 'student', // 'student' or 'instructor'
  setUser: (user) => set({ user }),
  setRole: (role) => {
    localStorage.setItem('userRole', role);
    set({ role });
  },
  logout: () => {
    localStorage.removeItem('userRole');
    set({ user: null, role: 'student' });
  },
}));

export const useSubmissionStore = create((set) => ({
  submissions: [],
  currentSubmission: null,
  loading: false,
  setSubmissions: (submissions) => set({ submissions }),
  setCurrentSubmission: (submission) => set({ currentSubmission: submission }),
  setLoading: (loading) => set({ loading }),
  addSubmission: (submission) =>
    set((state) => ({ submissions: [...state.submissions, submission] })),
}));

export const useAssignmentStore = create((set) => ({
  assignments: [],
  currentAssignment: null,
  loading: false,
  setAssignments: (assignments) => set({ assignments }),
  setCurrentAssignment: (assignment) => set({ currentAssignment: assignment }),
  setLoading: (loading) => set({ loading }),
}));
