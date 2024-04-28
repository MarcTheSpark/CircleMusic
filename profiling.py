

def start_profiling():
    # # START PROFILING
    import cProfile, pstats, io
    from pstats import SortKey
    pr = cProfile.Profile()
    pr.enable()



def stop_profiling(t):
    # # STOP AND PRINT PROFILING
    # Open a file for writing the profiling results
    with open('profiling_output.txt', 'w') as pro_file:
        sortby = SortKey.TIME
        ps = pstats.Stats(pr, stream=pro_file).sort_stats(sortby)

        # Print the stats directly to the file
        ps.print_stats()

    print("Profiling results saved to 'profiling_output.txt'")
